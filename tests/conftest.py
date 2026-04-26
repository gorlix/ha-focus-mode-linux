"""Shared test fixtures for Linux Focus Mode tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.linux_focus_mode.api import FocusModeApiClient
from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator

MOCK_STATE = {
    "active": True,
    "restore_enabled": True,
    "blocked_items": [
        {"name": "firefox", "type": "app"},
        {"name": "web.whatsapp.com", "type": "webapp"},
    ],
    "focus_lock": {
        "locked": False,
        "remaining_time": None,
        "target_time": None,
    },
}

MOCK_STATE_HA_LOCK = {
    **MOCK_STATE,
    "focus_lock": {"locked": True, "remaining_time": None, "target_time": None},
}

MOCK_STATE_TIMER_LOCK = {
    **MOCK_STATE,
    "focus_lock": {"locked": True, "remaining_time": "22m 14s", "target_time": None},
}

ENTRY_DATA = {
    "host": "192.168.1.100",
    "port": 8000,
    "token": "abcdef1234567890abcdef1234567890",
    "webhook_id": "linux_focus_mode_test1234",
}


@pytest.fixture
def mock_client() -> AsyncMock:
    """Return a mock API client with all methods stubbed."""
    client = AsyncMock(spec=FocusModeApiClient)
    client.async_get_state.return_value = MOCK_STATE
    client.async_toggle_blocker.return_value = {}
    client.async_lock_timer.return_value = {}
    client.async_lock_target.return_value = {}
    client.async_lock_ha.return_value = {}
    client.async_unlock.return_value = {}
    client.async_toggle_restore.return_value = {}
    return client
