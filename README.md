# Focus Mode for Home Assistant

> A Home Assistant Custom Component by [Alessandro Gorla (gorlix)](https://github.com/gorlix)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![HA Version](https://img.shields.io/badge/HA-2024.1.0%2B-blue)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

**Focus Mode for Home Assistant** is a custom integration that connects Home Assistant directly to a local **Focus Mode Linux companion application**, enabling full programmatic control over your machine's focus and productivity state from within your smart home ecosystem.

This integration was designed and built from the ground up to:
- **Toggle the Focus Mode blocker** on and off via a HA Switch entity, allowing you to trigger it from any automation, dashboard, voice assistant, or NFC tap.
- **Monitor active blocked items and focus lock status** via a HA Sensor entity with rich state attributes exposed for use in Jinja2 templates, Node-RED flows, and automations.
- **Synchronize dynamic notifications** from your Linux machine to Home Assistant in real time, bridging the gap between desktop productivity and home automation.
- **Trigger Do Not Disturb (DND) states** on your Linux environment programmatically from HA automations — for example, when a calendar event starts, when you sit at your desk, or when a button is pressed.

---

## ⚠️ Current Limitation: Linux Only

> **This integration is currently Linux-only.**

The Focus Mode companion backend runs as a local FastAPI service on your Linux machine. Windows and macOS are **not supported** at this time. The integration communicates with this backend over your local network via a REST API secured with a Bearer token.

---

## Companion App (Backend)

This integration requires the **Focus Mode Linux App** to be running on your local machine. You can find the companion application at:

> **[ha-focus-mode-linux](https://github.com/gorlix/ha-focus-mode-linux)** — The desktop companion app that runs the blocking engine and exposes the local REST API.

The backend must be started before adding this integration to Home Assistant. Refer to the companion app's documentation for setup instructions and how to retrieve your Bearer token.

---

## Features

| Entity | Type | Description |
|---|---|---|
| `switch.focus_mode_blocker` | Switch | Toggle Focus Mode blocking on and off |
| `sensor.focus_mode_blocked_items` | Sensor | Current number of active blocked items |

**Sensor Attributes** (available for Jinja2 / Node-RED):
```yaml
blocked_items:
  - name: "YouTube"
    type: "website"
  - name: "Discord"
    type: "application"
focus_lock:
  enabled: true
  locked_until: "2026-03-30T19:00:00"
```

---

## Installation

### Via HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Go to **Integrations** → click the **⋮** menu → **Custom repositories**.
3. Add `https://github.com/gorlix/ha-focus-mode-linux` as a custom repository of type **Integration**.
4. Search for **"Focus Mode"** and click **Download**.
5. **Restart** Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration** and search for **"Focus Mode"**.

### Manual

1. Download the latest release from the [Releases page](https://github.com/gorlix/ha-focus-mode-linux/releases).
2. Copy the `custom_components/focus_mode/` folder into your Home Assistant `config/custom_components/` directory.
3. **Restart** Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and search for **"Focus Mode"**.

---

## Configuration

During the UI setup, you will be prompted for:

| Field | Description | Example |
|---|---|---|
| **API Host URL** | The base URL of the Focus Mode backend | `http://192.168.1.100:8000` |
| **Bearer Token** | The 32-character authentication token from the companion app | `your-secret-token-here` |

The integration will perform a **live connection test** against your backend before saving the credentials. If the connection fails, an appropriate error will be displayed in the UI.

---

## Architecture

This integration follows strict Home Assistant asynchronous standards:

- **`aiohttp`** (via `async_get_clientsession`) is used exclusively for all HTTP communication. The synchronous `requests` library is **never** used.
- A **`DataUpdateCoordinator`** polls the backend every 30 seconds and delivers a single shared state snapshot to all entities simultaneously, avoiding redundant API calls.
- **`ConfigEntryAuthFailed`** is raised by the coordinator if the token is rejected, triggering HA's native re-authentication flow.

---

## License

MIT License. See [LICENSE](LICENSE) for details.