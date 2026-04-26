# Linux Focus Mode for Home Assistant

> A Home Assistant Custom Integration by [Alessandro Gorla (gorlix)](https://github.com/gorlix)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![HA Version](https://img.shields.io/badge/HA-2024.1.0%2B-blue)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Control and monitor the **Linux Focus Mode** productivity daemon directly from Home Assistant.
The integration exposes switches, sensors, binary sensors, and 8 services — all updated in
real time via push webhooks from the daemon.

---

## Prerequisites

- Home Assistant ≥ 2024.1.0
- [Focus Mode Linux App](https://github.com/gorlix/focus-mode-app-linux) running on your
  Linux machine (branch: `Home-Assistant-Integration`)
- HA instance reachable from the Linux machine (for webhook push)

---

## Installation

### Via HACS (recommended)

1. Open **HACS** → **Integrations** → **⋮** → **Custom repositories**.
2. Add `https://github.com/gorlix/ha-focus-mode-linux` — type **Integration**.
3. Search for **Linux Focus Mode** and click **Download**.
4. Restart Home Assistant.

### Manual

1. Download the latest release zip from the [Releases page](https://github.com/gorlix/ha-focus-mode-linux/releases).
2. Copy `custom_components/linux_focus_mode/` into your HA `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

Go to **Settings → Devices & Services → Add Integration** → search **Linux Focus Mode**.

### Step 1 — Connection

| Field | Description | Example |
|---|---|---|
| **Host** | IP address or hostname of the Linux machine | `192.168.1.100` |
| **Port** | API port (default 8000) | `8000` |
| **Bearer Token** | Token copied from the Linux app → Settings → HA Integration | `abcdef1234...` |

The integration validates the connection live before saving. On failure it shows the exact error.

### Step 2 — Webhook setup

After saving credentials, HA displays a **webhook URL** like:

```
https://your-ha-instance.local/api/webhook/linux_focus_mode_xxxxxxxx
```

Open the Linux app → **Settings → HA Integration** and paste this URL into **both** fields:
- **Webhook eventi di stato** (`state_event_url`)
- **Webhook dying gasp** (`dying_gasp_url`)

Using the same URL for both is correct — the integration distinguishes the two event types
by reading the `event` field in the JSON payload.

---

## Entities

### Switches

| Entity | Description |
|---|---|
| `switch.linux_focus_mode_focus_mode` | Toggle the process blocker on/off |
| `switch.linux_focus_mode_ha_lock` | Activate/deactivate the indefinite HA Lock |
| `switch.linux_focus_mode_auto_restore` | Enable/disable auto-restore of blocked apps |

> **Note:** Turning off the Focus Mode switch while HA Lock is active raises an error.
> Use the HA Lock switch (or `unlock` service) to remove the lock first.

### Sensors

| Entity | Description |
|---|---|
| `sensor.linux_focus_mode_blocked_apps_count` | Number of configured blocked items |
| `sensor.linux_focus_mode_lock_remaining_time` | Human-readable lock countdown, or `—` |

### Binary Sensors

| Entity | Description |
|---|---|
| `binary_sensor.linux_focus_mode_focus_locked` | `on` when any lock is active |
| `binary_sensor.linux_focus_mode_app_online` | `on` when daemon is reachable |

---

## Services

All services are callable from automations, scripts, and the Developer Tools.

| Service | Parameters | Description |
|---|---|---|
| `linux_focus_mode.focus_on` | — | Activate the blocker |
| `linux_focus_mode.focus_off` | — | Deactivate the blocker |
| `linux_focus_mode.lock_timer` | `minutes` (int, > 0) | Timer lock for N minutes |
| `linux_focus_mode.lock_target` | `hour` (0–23), `minute` (0–59) | Lock until HH:MM today |
| `linux_focus_mode.lock_ha` | — | Indefinite HA lock |
| `linux_focus_mode.unlock` | — | Cancel any active lock |
| `linux_focus_mode.restore_on` | — | Enable auto-restore |
| `linux_focus_mode.restore_off` | — | Disable auto-restore |

### Example automation — 25-minute Pomodoro

```yaml
automation:
  alias: "Start Pomodoro from button"
  trigger:
    - platform: state
      entity_id: input_button.start_pomodoro
  action:
    - service: linux_focus_mode.focus_on
    - service: linux_focus_mode.lock_timer
      data:
        minutes: 25
```

---

## How it works

```
Home Assistant ←──── push webhook on every state change ────── Linux daemon
     │                                                               ▲
     └──── GET /api/state every 30 s (fallback) ──────────────────►│
     └──── POST/DELETE /api/toggle|lock|restore (service calls) ───►│
```

- Push webhooks provide real-time updates (no 30 s wait).
- The 30 s polling is a fallback for missed webhooks.
- On app shutdown, a `dying_gasp` webhook marks all entities `unavailable` instantly.

---

## Troubleshooting

**Entities show `unavailable`**
- The daemon is not running or unreachable. Check that the Linux app is started.
- Verify host/port in the integration settings.

**Webhook not working (entities update only every 30 s)**
- Make sure the webhook URL is pasted into both fields of the Linux app settings.
- Verify your HA instance is reachable from the Linux machine (check firewall/Nabu Casa).

**"Cannot disable Focus Mode while HA Lock is active"**
- Turn off the HA Lock switch first, or call `linux_focus_mode.unlock`.

**Re-entering credentials**
- Go to **Settings → Devices & Services** → select the integration → **Configure**.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
