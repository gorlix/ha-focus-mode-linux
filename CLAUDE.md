# CLAUDE.md — Context for future Claude Code sessions

## What this repo is

Home Assistant custom integration (HACS) for the **Linux Focus Mode** project.

The Linux app is a productivity daemon that blocks distracting apps and websites.
All communication is **initiated by the Linux app** — HA never connects to the laptop.

This integration is the HA side of the bidirectional communication.

**Sister repo:** `https://github.com/gorlix/focus-mode-app-linux` (branch: `Home-Assistant-Integration`)
The complete API contract and behavioral spec is in `HACS_PLUGIN_SPEC.md`.

---

## Communication architecture

```
Linux app (laptop, dynamic IP)
  │
  │  POST /api/webhook/<webhook_id>   ← state push on every change
  │  POST /api/webhook/<webhook_id>   ← dying_gasp on shutdown
  ▼
Home Assistant webhook listener
  → coordinator.update_from_webhook() → entities re-render immediately

Home Assistant services / switches
  → hass.bus.async_fire("linux_focus_mode_command", {"action": "..."})
  → Linux app receives command via WebSocket subscription to HA event bus
```

**No REST polling. No host/IP/port stored. HA never connects to the laptop.**

---

## Repository layout

```
custom_components/linux_focus_mode/   ← DOMAIN = "linux_focus_mode"
├── __init__.py      setup_entry / unload_entry / service registration
├── manifest.json    HA manifest (iot_class: local_push)
├── const.py         DOMAIN, CONF_WEBHOOK_ID
├── api.py           Stub — only exception classes kept for compatibility
├── coordinator.py   FocusModeCoordinator — event-driven, update_interval=None
├── config_flow.py   Single step: user pastes webhook_id from the Linux app
├── webhook.py       HA webhook listener → coordinator.update_from_webhook()
├── switch.py        3 switches: active, ha_lock, restore
├── sensor.py        2 sensors: blocked_count, lock_remaining
├── binary_sensor.py 2 binary sensors: locked, app_online
├── services.yaml    8 service definitions with selectors
├── strings.json     UI strings (source of truth)
└── translations/    en.json, it.json
brand/icon.png       256×256 RGBA PNG
tests/               pytest test suite
```

---

## Running tests

```bash
# Create venv once
python -m venv /tmp/ha-focus-venv
/tmp/ha-focus-venv/bin/pip install -r requirements-dev.txt

# Run tests
/tmp/ha-focus-venv/bin/pytest tests/ --cov=custom_components/linux_focus_mode
```

The test framework is `pytest-homeassistant-custom-component`.
No live daemon needed — state is injected directly via `coordinator.data`.

---

## How state flows

1. Linux app pushes `POST /api/webhook/<webhook_id>` with one of:
   - `{"type": "update_sensor_states", "data": [...]}` — native app format
   - `{"event": "focus_toggled", "active": true}` — legacy format
   - `{"event": "dying_gasp"}` — shutdown signal
2. `webhook.py` receives it and calls `coordinator.update_from_webhook(data)`
   or `coordinator.set_unavailable()` for dying_gasp.
3. `coordinator.async_set_updated_data(parsed)` notifies all subscribed entities.

## How commands flow

1. User calls a service or toggles a switch in HA.
2. `hass.bus.async_fire("linux_focus_mode_command", {"action": "focus_on"})`.
3. Linux app receives the event via its persistent WebSocket subscription.

---

## Adding a new entity

1. Choose the right platform file (`switch.py`, `sensor.py`, `binary_sensor.py`).
2. Subclass `_FocusModeBase*Entity` (already defined in each file).
3. Set `_attr_translation_key` to a new key and add it to `strings.json` + `translations/`.
4. Add a `unique_id` as `f"{entry.entry_id}_<new_suffix>"`.
5. Add the new class to `async_setup_entry` in that platform file.
6. Write a test in `tests/test_<platform>.py`.

---

## Adding a new service

1. Add the service definition to `services.yaml`.
2. Register it in `_register_services()` in `__init__.py` following the existing pattern.
   Fire the event: `hass.bus.async_fire("linux_focus_mode_command", {"action": "..."})`.
3. Write a test in `tests/test_services.py`.

---

## Behavioral constraints

- **HA Lock** is indefinite — only the `unlock` service removes it.
- **Active switch turn_off** raises `HomeAssistantError` when HA Lock is engaged.
- **Commands are fire-and-forget** — never update entity state from the command;
  wait for the app to push back state via webhook.
- **dying_gasp webhook** → `coordinator.set_unavailable()` immediately.
- The same HA webhook URL goes into **both** `state_event_url` and `dying_gasp_url`
  in the Linux app settings.

---

## Publishing a new release

```bash
# 1. Bump version in manifest.json
# 2. Add entry to CHANGELOG.md
# 3. Commit and push
git tag v1.x.0
git push origin v1.x.0
# 4. Create GitHub Release from the tag — HACS picks it up automatically
```
