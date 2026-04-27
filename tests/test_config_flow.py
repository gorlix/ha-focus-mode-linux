"""Tests for the config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.linux_focus_mode.const import DOMAIN

from .conftest import ENTRY_DATA


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return enable_custom_integrations


async def _start_flow(hass: HomeAssistant) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    return result


async def test_config_flow_success(hass: HomeAssistant) -> None:
    """Happy path: valid webhook_id creates entry."""
    result = await _start_flow(hass)

    with patch(
        "custom_components.linux_focus_mode.config_flow.async_generate_url",
        return_value=ENTRY_DATA["webhook_url"],
    ), patch(
        "custom_components.linux_focus_mode.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"webhook_id": ENTRY_DATA["webhook_id"]},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["webhook_id"] == ENTRY_DATA["webhook_id"]
    assert result["data"]["webhook_url"] == ENTRY_DATA["webhook_url"]


async def test_config_flow_empty_webhook_id(hass: HomeAssistant) -> None:
    """Empty/blank webhook_id — form re-shown with invalid_webhook_id error."""
    result = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"webhook_id": "   "},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["webhook_id"] == "invalid_webhook_id"


async def test_config_flow_shows_user_step(hass: HomeAssistant) -> None:
    """Initial flow shows the user step with webhook_id field."""
    result = await _start_flow(hass)
    assert "webhook_id" in result["data_schema"].schema
