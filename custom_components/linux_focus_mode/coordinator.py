"""Data update coordinator for the Linux Focus Mode integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    FocusModeApiClient,
    FocusModeApiAuthenticationError,
    FocusModeApiCommunicationError,
    FocusModeApiError,
)
from .const import DEFAULT_POLLING_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class FocusModeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Single polling source for all Linux Focus Mode entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: FocusModeApiClient,
        interval: timedelta = DEFAULT_POLLING_INTERVAL,
    ) -> None:
        """Initialize.

        Args:
            hass: Home Assistant core instance.
            client: Configured FocusModeApiClient.
            interval: Polling interval (default 30 s).
        """
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=interval,
        )
        self.client = client
        self.available: bool = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch daemon state — called automatically by the coordinator on each cycle."""
        try:
            data = await self.client.async_get_state()
            self.available = True
            return data
        except FocusModeApiAuthenticationError as err:
            self.available = False
            raise ConfigEntryAuthFailed from err
        except FocusModeApiCommunicationError as err:
            self.available = False
            raise UpdateFailed(f"Communication error: {err}") from err
        except FocusModeApiError as err:
            self.available = False
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            self.available = False
            _LOGGER.exception("Unexpected error fetching Focus Mode data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def set_unavailable(self) -> None:
        """Mark the daemon offline and notify all subscriber entities immediately.

        Called when a dying_gasp webhook is received. Uses async_set_updated_data
        so entities re-render without waiting for the next polling cycle.
        """
        self.available = False
        self.async_set_updated_data(self.data or {})
