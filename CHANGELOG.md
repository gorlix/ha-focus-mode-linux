# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] — 2026-04-26

### Added

- Config flow with separate host / port / token fields and live connection validation
- Step 2 in config flow displays the HA webhook URL to copy into the Linux app
- `FocusModeApiClient` with all REST methods: `toggle`, `lock_timer`, `lock_target`,
  `lock_ha`, `unlock`, `toggle_restore`
- `FocusModeCoordinator` with `available` flag and `set_unavailable()` for dying-gasp
- Webhook listener (`/api/webhook/<id>`) for push events from the daemon:
  - `dying_gasp` → immediate offline marking of all entities
  - all other events → immediate coordinator refresh (no waiting for 30 s poll)
- **Switches:** Focus Mode (active), HA Lock, Auto-Restore
  - Active switch raises `HomeAssistantError` when turn_off is attempted during HA Lock
- **Sensors:** Blocked Apps Count, Lock Remaining Time
- **Binary sensors:** Focus Locked, App Online
- **8 HA services:** `focus_on`, `focus_off`, `lock_timer`, `lock_target`, `lock_ha`,
  `unlock`, `restore_on`, `restore_off`
- Full test suite with `pytest-homeassistant-custom-component` (coverage ≥ 80 %)
- HACS Action CI workflow and pytest CI workflow
- English and Italian translations
- `brand/icon.png` 256 × 256 integration icon
