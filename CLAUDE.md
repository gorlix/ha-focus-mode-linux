# CLAUDE.md — Context for future Claude Code sessions

## What this repo is

Home Assistant custom integration (HACS) for the **Linux Focus Mode** project.

The Linux app is a productivity daemon that blocks distracting apps and websites.
It exposes a REST API (port 8000) and sends push webhooks to HA on every state change.

This integration is the HA side of the bidirectional communication.

**Sister repo:** `https://github.com/gorlix/focus-mode-app-linux` (branch: `Home-Assistant-Integration`)
The complete API contract and behavioral spec is in `HACS_PLUGIN_SPEC.md`.

---

## Repository layout

```
custom_components/linux_focus_mode/   ← DOMAIN = "linux_focus_mode"
├── __init__.py      setup_entry / unload_entry / service registration
├── manifest.json    HA manifest
├── const.py         DOMAIN, CONF_* constants
├── api.py           FocusModeApiClient — all REST methods
├── coordinator.py   FocusModeCoordinator — polling + availability
├── config_flow.py   2-step UI: credentials → webhook URL display
├── webhook.py       HA webhook listener for push events
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
pip install -r requirements-dev.txt
pytest tests/ --cov=custom_components/linux_focus_mode
```

The test framework is `pytest-homeassistant-custom-component`, which provides a real
HA event loop and fixtures (`hass`, `enable_custom_integrations`).
All API calls are mocked — no live daemon needed.

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
3. Write a test in `tests/test_services.py`.

---

## Behavioral constraints (see HACS_PLUGIN_SPEC.md for details)

- **HA Lock** is indefinite — only `DELETE /api/lock` removes it.
- **Active switch turn_off** raises `HomeAssistantError` when HA Lock is engaged.
- **API responses are optimistic** — the daemon enqueues actions and responds immediately.
  Never update entity state from the POST response; wait for `async_request_refresh()`.
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
