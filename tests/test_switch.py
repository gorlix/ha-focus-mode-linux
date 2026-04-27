"""Tests for the switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.linux_focus_mode.coordinator import FocusModeCoordinator
from custom_components.linux_focus_mode.switch import (
    FocusModeActiveSwitch,
    FocusModeHaLockSwitch,
    FocusModeRestoreSwitch,
)

from .conftest import MOCK_STATE, MOCK_STATE_HA_LOCK, MOCK_STATE_TIMER_LOCK

_EVENT = "linux_focus_mode_command"


def _make_entry():
    entry = AsyncMock()
    entry.entry_id = "test_entry_id"
    return entry


def _make_coordinator(hass: HomeAssistant, state: dict) -> FocusModeCoordinator:
    coordinator = FocusModeCoordinator(hass)
    coordinator.data = state
    coordinator.available = True
    return coordinator


def _make_switch(hass, cls, state=None):
    coordinator = _make_coordinator(hass, state or MOCK_STATE)
    sw = cls(coordinator, _make_entry())
    sw.hass = hass
    return sw


def _listen(hass: HomeAssistant) -> list:
    fired = []
    hass.bus.async_listen(_EVENT, lambda e: fired.append(dict(e.data)))
    return fired


# ── Active switch ──────────────────────────────────────────────────────────────

async def test_active_switch_is_on(hass: HomeAssistant) -> None:
    assert _make_switch(hass, FocusModeActiveSwitch).is_on is True


async def test_active_switch_is_off(hass: HomeAssistant) -> None:
    sw = _make_switch(hass, FocusModeActiveSwitch, {**MOCK_STATE, "active": False})
    assert sw.is_on is False


async def test_active_switch_turn_on_fires_event(hass: HomeAssistant) -> None:
    fired = _listen(hass)
    await _make_switch(hass, FocusModeActiveSwitch).async_turn_on()
    await hass.async_block_till_done()
    assert fired == [{"action": "focus_on"}]


async def test_active_switch_turn_off_fires_event(hass: HomeAssistant) -> None:
    fired = _listen(hass)
    await _make_switch(hass, FocusModeActiveSwitch).async_turn_off()
    await hass.async_block_till_done()
    assert fired == [{"action": "focus_off"}]


async def test_active_switch_turn_off_blocked_by_ha_lock(hass: HomeAssistant) -> None:
    fired = _listen(hass)
    sw = _make_switch(hass, FocusModeActiveSwitch, MOCK_STATE_HA_LOCK)
    with pytest.raises(HomeAssistantError):
        await sw.async_turn_off()
    assert fired == []


async def test_active_switch_turn_off_allowed_with_timer_lock(hass: HomeAssistant) -> None:
    fired = _listen(hass)
    await _make_switch(hass, FocusModeActiveSwitch, MOCK_STATE_TIMER_LOCK).async_turn_off()
    await hass.async_block_till_done()
    assert fired == [{"action": "focus_off"}]


# ── HA Lock switch ─────────────────────────────────────────────────────────────

async def test_ha_lock_switch_is_on(hass: HomeAssistant) -> None:
    assert _make_switch(hass, FocusModeHaLockSwitch, MOCK_STATE_HA_LOCK).is_on is True


async def test_ha_lock_switch_off_with_timer_lock(hass: HomeAssistant) -> None:
    assert _make_switch(hass, FocusModeHaLockSwitch, MOCK_STATE_TIMER_LOCK).is_on is False


async def test_ha_lock_turn_on_fires_event(hass: HomeAssistant) -> None:
    fired = _listen(hass)
    await _make_switch(hass, FocusModeHaLockSwitch).async_turn_on()
    await hass.async_block_till_done()
    assert fired == [{"action": "lock_ha"}]


async def test_ha_lock_turn_off_fires_event(hass: HomeAssistant) -> None:
    fired = _listen(hass)
    await _make_switch(hass, FocusModeHaLockSwitch).async_turn_off()
    await hass.async_block_till_done()
    assert fired == [{"action": "unlock"}]


# ── Restore switch ─────────────────────────────────────────────────────────────

async def test_restore_switch_is_on(hass: HomeAssistant) -> None:
    assert _make_switch(hass, FocusModeRestoreSwitch).is_on is True


async def test_restore_switch_turn_on_fires_event(hass: HomeAssistant) -> None:
    fired = _listen(hass)
    await _make_switch(hass, FocusModeRestoreSwitch).async_turn_on()
    await hass.async_block_till_done()
    assert fired == [{"action": "restore_on"}]


async def test_restore_switch_turn_off_fires_event(hass: HomeAssistant) -> None:
    fired = _listen(hass)
    await _make_switch(hass, FocusModeRestoreSwitch).async_turn_off()
    await hass.async_block_till_done()
    assert fired == [{"action": "restore_off"}]


# ── Availability ───────────────────────────────────────────────────────────────

async def test_switch_unavailable_when_coordinator_offline(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, MOCK_STATE)
    coordinator.set_unavailable()
    sw = FocusModeActiveSwitch(coordinator, _make_entry())
    assert sw.available is False
