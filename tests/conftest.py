"""Shared test fixtures for Linux Focus Mode tests."""

from __future__ import annotations

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
    "webhook_id": "linux_focus_mode_test1234",
    "webhook_url": "http://ha.local/api/webhook/linux_focus_mode_test1234",
}
