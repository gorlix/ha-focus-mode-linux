"""Config flow for the Focus Mode integration.

This module manages the user interface within Home Assistant for adding and configuring
the Focus Mode integration. It handles user input mapping, connection validation,
and creating the final ConfigEntry.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    FocusModeApiClient,
    FocusModeApiAuthenticationError,
    FocusModeApiCommunicationError,
    FocusModeApiError,
)
from .const import CONF_HOST, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

# The data schema defines the structure of the UI form presented to the user.
# vol.Required marks fields as mandatory, and we provide a reasonable default
# for the host URL to guide the user towards the expected format.
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="http://localhost:8000"): str,
        vol.Required(CONF_TOKEN): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate that the user input enables a successful API connection.

    We separate this validation logic from the main config flow step to keep the
    architectural boundary clean. The flow is strictly for managing UI transitions,
    while this function focuses on instantiating the API client and testing the
    connection.

    Args:
        hass: The core Home Assistant instance.
        data: The dictionary of user-provided configuration data mapped by CONF_* keys.

    Returns:
        A dictionary containing info to be stored in the config entry, such as a
        friendly server title.

    Raises:
        FocusModeApiAuthenticationError: If the provided token is rejected.
        FocusModeApiCommunicationError: If the host is unreachable.
        FocusModeApiError: If an unexpected API error occurs.
    """
    # Obtain the shared aiohttp websession. Doing this ensures efficient connection
    # pooling and respects the global Home Assistant proxy and SSL configurations.
    session = async_get_clientsession(hass)

    client = FocusModeApiClient(
        host=data[CONF_HOST],
        token=data[CONF_TOKEN],
        session=session,
    )

    # Perform a live query against the backend. If this fails, the appropriate
    # custom exception will be raised, caught by async_step_user, and translated
    # into a user-friendly error message in the UI.
    await client.async_get_state()

    # Return arbitrary data that might be useful when creating the entry,
    # in this case a default title for the integration instance.
    return {"title": "Focus Mode"}


class FocusModeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for integrating Focus Mode.

    This class manages the lifecycle of the config UI. It inherits from `ConfigFlow`
    and binds to the DOMAIN from our constants.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial user input step.

        This method is called when the user first adds the integration, or when
        they submit the form.

        Args:
            user_input: Provided by the UI form on submission. It will be None when
                the form is initially loaded.

        Returns:
            A FlowResult dictionary instructing Home Assistant on what to do next
            (e.g., show a form, create an entry, abort).
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # The user submitted the form. We attempt to validate their input.
            try:
                info = await validate_input(self.hass, user_input)
            except FocusModeApiCommunicationError:
                # The host couldn't be reached or timed out.
                # Map to the 'cannot_connect' key in strings.json.
                errors["base"] = "cannot_connect"
            except FocusModeApiAuthenticationError:
                # The token was rejected (HTTP 401/403).
                # Map to the 'invalid_auth' key in strings.json.
                errors["base"] = "invalid_auth"
            except FocusModeApiError:
                # Catch-all for our custom API errors.
                errors["base"] = "unknown"
            except Exception:  # pylint: disable=broad-except
                # We log unexpected, non-API exceptions internally to help with
                # debugging, but present a generic error to the user to maintain UX.
                _LOGGER.exception("Unexpected exception occurred during validation")
                errors["base"] = "unknown"
            else:
                # Validation succeeded without exceptions.
                # We proceed to create the ConfigEntry, passing the validated data.
                return self.async_create_entry(title=info["title"], data=user_input)

        # If we reach here, it's either the first load (user_input is None) OR
        # validation failed (errors is not empty). In both cases, we show the form.
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
