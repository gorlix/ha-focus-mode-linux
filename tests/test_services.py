"""Tests for the registered HA services."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.linux_focus_mode import _register_services
from custom_components.linux_focus_mode.const import DOMAIN

_EVENT = "linux_focus_mode_command"


def _setup(hass: HomeAssistant) -> list:
    fired = []
    hass.bus.async_listen(_EVENT, lambda e: fired.append(dict(e.data)))
    _register_services(hass)
    return fired


async def test_service_focus_on(hass: HomeAssistant) -> None:
    fired = _setup(hass)
    await hass.services.async_call(DOMAIN, "focus_on", {}, blocking=True)
    await hass.async_block_till_done()
    assert fired == [{"action": "focus_on"}]


async def test_service_focus_off(hass: HomeAssistant) -> None:
    fired = _setup(hass)
    await hass.services.async_call(DOMAIN, "focus_off", {}, blocking=True)
    await hass.async_block_till_done()
    assert fired == [{"action": "focus_off"}]


async def test_service_lock_timer(hass: HomeAssistant) -> None:
    fired = _setup(hass)
    await hass.services.async_call(DOMAIN, "lock_timer", {"minutes": 25}, blocking=True)
    await hass.async_block_till_done()
    assert fired == [{"action": "lock_timer", "minutes": 25}]


async def test_service_lock_target(hass: HomeAssistant) -> None:
    fired = _setup(hass)
    await hass.services.async_call(
        DOMAIN, "lock_target", {"hour": 14, "minute": 30}, blocking=True
    )
    await hass.async_block_till_done()
    assert fired == [{"action": "lock_target", "hour": 14, "minute": 30}]


async def test_service_lock_ha(hass: HomeAssistant) -> None:
    fired = _setup(hass)
    await hass.services.async_call(DOMAIN, "lock_ha", {}, blocking=True)
    await hass.async_block_till_done()
    assert fired == [{"action": "lock_ha"}]


async def test_service_unlock(hass: HomeAssistant) -> None:
    fired = _setup(hass)
    await hass.services.async_call(DOMAIN, "unlock", {}, blocking=True)
    await hass.async_block_till_done()
    assert fired == [{"action": "unlock"}]


async def test_service_restore_on(hass: HomeAssistant) -> None:
    fired = _setup(hass)
    await hass.services.async_call(DOMAIN, "restore_on", {}, blocking=True)
    await hass.async_block_till_done()
    assert fired == [{"action": "restore_on"}]


async def test_service_restore_off(hass: HomeAssistant) -> None:
    fired = _setup(hass)
    await hass.services.async_call(DOMAIN, "restore_off", {}, blocking=True)
    await hass.async_block_till_done()
    assert fired == [{"action": "restore_off"}]
