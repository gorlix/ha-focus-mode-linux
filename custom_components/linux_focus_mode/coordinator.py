"""Data update coordinator for the Focus Mode integration.

This module acts as the central state manager for the integration. Instead of having
each entity (switch and sensor) poll the backend independently—which would multiply
API requests and violate Home Assistant best practices—the coordinator fetches the
data once per interval and pushes updates to all subscribed entities simultaneously.
"""

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
    """Class to manage fetching Focus Mode data asynchronously.

    Inherits from `DataUpdateCoordinator` to take advantage of Home Assistant's
    built-in functionality for periodic polling, debouncing rapid refresh requests,
    and handling listener subscriptions.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: FocusModeApiClient,
        interval: timedelta = DEFAULT_POLLING_INTERVAL,
    ) -> None:
        """Initialize the Focus Mode DataUpdateCoordinator.

        Args:
            hass: The Home Assistant core instance.
            client: The pre-configured FocusModeApiClient connected to the user's backend.
            interval: How frequently to poll the backend. Defaults to 30 seconds.
        """
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=interval,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest state from the Focus Mode API.

        This method is invoked automatically by the coordinator based on the
        `update_interval`, or manually via `async_request_refresh()`.

        Returns:
            The raw JSON state dictionary (`{"active": bool, "blocked_items": [...], ...}`)
            which will be stored in `self.data`.

        Raises:
            ConfigEntryAuthFailed: If the backend rejects our token (e.g., HTTP 401).
                Home Assistant catches this specifically to trigger the reauth flow
                and prompt the user to enter a new token.
            UpdateFailed: Standard Home Assistant exception indicating that this
                specific polling cycle failed (e.g., due to a timeout or crash).
                Entities will transition to an "Unavailable" state until the next
                successful poll.
        """
        try:
            # We rely entirely on the robust exception handling built into our API wrapper.
            # If `async_get_state` completes successfully, it returns the parsed JSON dict.
            return await self.client.async_get_state()

        except FocusModeApiAuthenticationError as err:
            # Raising ConfigEntryAuthFailed is a critical architectural pattern.
            # It alerts the Home Assistant core that the integration is fundamentally broken
            # due to credentials, prompting intervention rather than endless failing polls.
            raise ConfigEntryAuthFailed from err

        except FocusModeApiCommunicationError as err:
            # A timeout or connection refusal. We raise UpdateFailed so the system
            # knows the integration is offline temporarily.
            raise UpdateFailed(
                f"Communication error with Focus Mode API: {err}"
            ) from err

        except FocusModeApiError as err:
            # Catch-all for our custom exceptions to ensure we gracefully handle
            # unexpected payloads or edge cases.
            raise UpdateFailed(f"Unknown Focus Mode API error: {err}") from err

        except Exception as err:  # pylint: disable=broad-except
            # Defensive programming: If an absolute catastrophe happens in the client,
            # we log it loudly and fail the update, rather than crashing the polling loop.
            _LOGGER.exception("Unexpected error fetching Focus Mode data")
            raise UpdateFailed(f"Unexpected error: {err}") from err
