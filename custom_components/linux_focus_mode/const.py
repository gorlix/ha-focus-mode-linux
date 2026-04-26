"""Constants for the Linux Focus Mode integration."""

from datetime import timedelta

DOMAIN = "linux_focus_mode"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_TOKEN = "token"

DEFAULT_PORT = 8000
DEFAULT_POLLING_INTERVAL = timedelta(seconds=30)
