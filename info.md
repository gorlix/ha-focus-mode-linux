# Linux Focus Mode

> [!IMPORTANT]
> **COMPANION APP REQUIRED**
> This Home Assistant integration is strictly an interface. It does **not** do anything on its own. To function, it requires the [Linux Focus Mode App](https://github.com/gorlix/focus-mode-app-linux) to be installed and running on your Linux machine.

Control and monitor your Linux Focus Mode productivity daemon directly from Home Assistant. The integration communicates bidirectionally in real-time, allowing you to block distracting apps and websites, set Pomodoro timers, and trigger automation locks from your smart home.

## 🚀 Features

- **Real-Time Sync**: Instant state updates pushed from your PC to Home Assistant via webhooks. No polling delays!
- **Switches**: Toggle Focus Mode, enable HA Lock (indefinite lock), and toggle Auto-Restore for blocked apps.
- **Sensors**: Monitor the exact number of blocked items and see a live countdown for active lock timers.
- **Binary Sensors**: Instantly know if your PC's Focus Mode is locked and whether the daemon is online.
- **Services**: Full control through automations (e.g., trigger `linux_focus_mode.lock_timer` for a 25-minute Pomodoro session with a physical smart button).

## 📖 Setup Instructions

For step-by-step installation and configuration instructions (including webhook setup), please refer to the [official README](https://github.com/gorlix/ha-focus-mode-linux/blob/main/README.md) in the repository.
