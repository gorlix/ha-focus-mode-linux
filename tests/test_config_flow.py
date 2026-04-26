"""Tests for the config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.linux_focus_mode.api import (
    FocusModeApiAuthenticationError,
    FocusModeApiCommunicationError,
)
from custom_components.linux_focus_mode.const import DOMAIN

from .conftest import ENTRY_DATA


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for tests."""
    return enable_custom_integrations


async def _start_flow(hass: HomeAssistant) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    return result


async def test_config_flow_success(hass: HomeAssistant) -> None:
    """Happy path: valid credentials proceed to webhook step then create entry."""
    result = await _start_flow(hass)

    with patch(
        "custom_components.linux_focus_mode.config_flow.FocusModeApiClient"
    ) as MockClient, patch(
        "custom_components.linux_focus_mode.config_flow.async_generate_url",
        return_value="http://ha.local/api/webhook/test",
    ):
        mock_instance = AsyncMock()
        mock_instance.async_get_state.return_value = {}
        MockClient.return_value = mock_instance

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "host": ENTRY_DATA["host"],
                "port": ENTRY_DATA["port"],
                "token": ENTRY_DATA["token"],
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "webhook"

    # Patch async_setup_entry so HA does not attempt a real connection on entry creation.
    with patch(
        "custom_components.linux_focus_mode.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == ENTRY_DATA["host"]
    assert "webhook_id" in result["data"]


async def test_config_flow_invalid_auth(hass: HomeAssistant) -> None:
    """Token rejected — form re-shown with invalid_auth error."""
    result = await _start_flow(hass)

    with patch(
        "custom_components.linux_focus_mode.config_flow.FocusModeApiClient"
    ) as MockClient:
        mock_instance = AsyncMock()
        mock_instance.async_get_state.side_effect = FocusModeApiAuthenticationError
        MockClient.return_value = mock_instance

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.1", "port": 8000, "token": "bad"},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


async def test_config_flow_cannot_connect(hass: HomeAssistant) -> None:
    """Host unreachable — form re-shown with cannot_connect error."""
    result = await _start_flow(hass)

    with patch(
        "custom_components.linux_focus_mode.config_flow.FocusModeApiClient"
    ) as MockClient:
        mock_instance = AsyncMock()
        mock_instance.async_get_state.side_effect = FocusModeApiCommunicationError
        MockClient.return_value = mock_instance

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "10.0.0.99", "port": 8000, "token": "tok"},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"
