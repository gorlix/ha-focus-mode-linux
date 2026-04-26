"""Config flow for the Linux Focus Mode integration."""

from __future__ import annotations

import logging
import secrets
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.webhook import async_generate_url
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    FocusModeApiAuthenticationError,
    FocusModeApiClient,
    FocusModeApiCommunicationError,
    FocusModeApiError,
)
from .const import CONF_HOST, CONF_PORT, CONF_TOKEN, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_WEBHOOK_ID = "webhook_id"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Required(CONF_TOKEN): str,
    }
)


class LinuxFocusModeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Linux Focus Mode."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow state."""
        self._user_input: dict[str, Any] = {}
        self._webhook_id: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1 — connection credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                client = FocusModeApiClient(
                    host=user_input[CONF_HOST],
                    port=user_input[CONF_PORT],
                    token=user_input[CONF_TOKEN],
                    session=session,
                )
                await client.async_get_state()
            except FocusModeApiCommunicationError:
                errors["base"] = "cannot_connect"
            except FocusModeApiAuthenticationError:
                errors["base"] = "invalid_auth"
            except FocusModeApiError:
                errors["base"] = "unknown"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow validation")
                errors["base"] = "unknown"
            else:
                self._user_input = user_input
                self._webhook_id = f"linux_focus_mode_{secrets.token_hex(8)}"
                return await self.async_step_webhook()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_webhook(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2 — display webhook URL to copy into the Linux app."""
        if user_input is not None:
            entry_data = dict(self._user_input)
            entry_data[CONF_WEBHOOK_ID] = self._webhook_id
            return self.async_create_entry(
                title=f"Linux Focus Mode ({self._user_input[CONF_HOST]})",
                data=entry_data,
            )

        webhook_url = async_generate_url(self.hass, self._webhook_id)

        return self.async_show_form(
            step_id="webhook",
            description_placeholders={"webhook_url": webhook_url},
        )
