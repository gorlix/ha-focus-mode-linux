"""Stub: API Client removed in favour of Native App Integration.

All communication is now initiated by the Linux app:
- State push  → POST /api/webhook/<webhook_id>  (native app format)
- Commands    → received via HA event bus (linux_focus_mode_command)

This file is kept only so external code that catches FocusModeApiError
continues to compile without changes.
"""


class FocusModeApiError(Exception):
    """Base exception (kept for compatibility)."""


class FocusModeApiCommunicationError(FocusModeApiError):
    """Kept for compatibility."""


class FocusModeApiAuthenticationError(FocusModeApiError):
    """Kept for compatibility."""
