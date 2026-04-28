"""Tests for the event-driven coordinator."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.linux_focus_mode.coordinator import (
    FocusModeCoordinator,
    _parse_webhook_payload,
)

from .conftest import MOCK_STATE


async def test_update_from_webhook_native_format(hass: HomeAssistant) -> None:
    """Native app update_sensor_states payload sets available=True and updates data."""
    coordinator = FocusModeCoordinator(hass)
    payload = {
        "type": "update_sensor_states",
        "data": [
            {"unique_id": "focus_active", "state": True, "type": "binary_sensor"},
            {"unique_id": "restore_enabled", "state": True, "type": "binary_sensor"},
            {"unique_id": "blocked_count", "state": 3, "type": "sensor"},
        ],
    }
    coordinator.update_from_webhook(payload)
    assert coordinator.available is True
    assert coordinator.data["active"] is True
    assert coordinator.data["restore_enabled"] is True


async def test_update_from_webhook_legacy_focus_toggle(hass: HomeAssistant) -> None:
    """Legacy focus_toggled event updates active state."""
    coordinator = FocusModeCoordinator(hass)
    coordinator.update_from_webhook({"event": "focus_toggled", "active": True})
    assert coordinator.available is True
    assert coordinator.data["active"] is True

    coordinator.update_from_webhook({"event": "focus_toggled", "active": False})
    assert coordinator.data["active"] is False


async def test_update_from_webhook_restore_changed(hass: HomeAssistant) -> None:
    """Legacy restore_changed event updates restore_enabled."""
    coordinator = FocusModeCoordinator(hass)
    coordinator.update_from_webhook({"event": "restore_changed", "enabled": False})
    assert coordinator.data["restore_enabled"] is False


async def test_set_unavailable(hass: HomeAssistant) -> None:
    """set_unavailable marks available=False while preserving data."""
    coordinator = FocusModeCoordinator(hass)
    coordinator.update_from_webhook({"event": "focus_toggled", "active": True})
    assert coordinator.available is True

    coordinator.set_unavailable()
    assert coordinator.available is False
    assert coordinator.data is not None


async def test_recovers_after_unavailable(hass: HomeAssistant) -> None:
    """After set_unavailable, next webhook push restores available=True."""
    coordinator = FocusModeCoordinator(hass)
    coordinator.set_unavailable()
    assert coordinator.available is False

    coordinator.update_from_webhook({"event": "focus_toggled", "active": True})
    assert coordinator.available is True


def test_parse_native_ha_lock() -> None:
    """ha_lock_active=True sets locked=True and remaining_time=None."""
    base = {**MOCK_STATE, "focus_lock": dict(MOCK_STATE["focus_lock"])}
    payload = {
        "type": "update_sensor_states",
        "data": [
            {"unique_id": "ha_lock_active", "state": True, "type": "binary_sensor"}
        ],
    }
    result = _parse_webhook_payload(payload, base)
    assert result["focus_lock"]["locked"] is True
    assert result["focus_lock"]["remaining_time"] is None


def test_parse_lock_remaining() -> None:
    """lock_remaining sensor updates remaining_time."""
    base = {"focus_lock": {"locked": True, "remaining_time": None, "target_time": None}}
    payload = {
        "type": "update_sensor_states",
        "data": [{"unique_id": "lock_remaining", "state": "22m 14s", "type": "sensor"}],
    }
    result = _parse_webhook_payload(payload, base)
    assert result["focus_lock"]["remaining_time"] == "22m 14s"


def test_parse_lock_remaining_dash_becomes_none() -> None:
    """lock_remaining with '—' sentinel is normalised to None."""
    base = {"focus_lock": {"locked": True, "remaining_time": "5m", "target_time": None}}
    payload = {
        "type": "update_sensor_states",
        "data": [{"unique_id": "lock_remaining", "state": "—", "type": "sensor"}],
    }
    result = _parse_webhook_payload(payload, base)
    assert result["focus_lock"]["remaining_time"] is None


def test_parse_focus_active_sensor() -> None:
    """focus_active sensor maps to data['active']."""
    base = {"active": False, "focus_lock": {}}
    payload = {
        "type": "update_sensor_states",
        "data": [{"unique_id": "focus_active", "state": True}],
    }
    result = _parse_webhook_payload(payload, base)
    assert result["active"] is True
