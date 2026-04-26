"""API Client for the Linux Focus Mode integration."""

from __future__ import annotations

import asyncio
import socket
from typing import Any

import aiohttp


class FocusModeApiError(Exception):
    """Base exception for all Focus Mode API errors."""


class FocusModeApiCommunicationError(FocusModeApiError):
    """Raised when a network communication error occurs (timeout, refused, DNS)."""


class FocusModeApiAuthenticationError(FocusModeApiError):
    """Raised when the bearer token is rejected (HTTP 401/403)."""


class FocusModeApiClient:
    """Async client for the Focus Mode daemon REST API."""

    def __init__(
        self, host: str, port: int, token: str, session: aiohttp.ClientSession
    ) -> None:
        """Initialize the client.

        Args:
            host: IP address or hostname of the Linux machine.
            port: API port (typically 8000).
            token: 32-character bearer token from the daemon.
            session: Shared aiohttp session from `async_get_clientsession`.
        """
        self._base_url = f"http://{host}:{port}"
        self._token = token
        self._session = session

    async def _api_wrapper(
        self, method: str, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Perform an authenticated HTTP request and return the JSON response.

        Raises:
            FocusModeApiAuthenticationError: On HTTP 401/403.
            FocusModeApiCommunicationError: On timeout or connection failure.
            FocusModeApiError: On any other unexpected error.
        """
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with asyncio.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=f"{self._base_url}{path}",
                    headers=headers,
                    json=data,
                )
                if response.status in (401, 403):
                    raise FocusModeApiAuthenticationError("Invalid credentials")
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError as err:
            raise FocusModeApiCommunicationError("Timeout connecting to daemon") from err
        except (aiohttp.ClientError, socket.gaierror) as err:
            raise FocusModeApiCommunicationError("Cannot connect to daemon") from err
        except FocusModeApiAuthenticationError:
            raise
        except Exception as err:
            raise FocusModeApiError(f"Unexpected API error: {err}") from err

    # ── Read ──────────────────────────────────────────────────────────────────

    async def async_get_state(self) -> dict[str, Any]:
        """GET /api/state — full daemon state snapshot."""
        return await self._api_wrapper("GET", "/api/state")

    # ── Blocker toggle ────────────────────────────────────────────────────────

    async def async_toggle_blocker(self, active: bool) -> dict[str, Any]:
        """POST /api/toggle — activate or deactivate the process blocker."""
        return await self._api_wrapper("POST", "/api/toggle", data={"active": active})

    # ── Lock ──────────────────────────────────────────────────────────────────

    async def async_lock_timer(self, minutes: int) -> dict[str, Any]:
        """POST /api/lock — timer lock for N minutes."""
        return await self._api_wrapper(
            "POST", "/api/lock", data={"mode": "timer", "minutes": minutes}
        )

    async def async_lock_target(self, hour: int, minute: int) -> dict[str, Any]:
        """POST /api/lock — target-time lock until HH:MM today (or tomorrow)."""
        return await self._api_wrapper(
            "POST", "/api/lock", data={"mode": "target", "hour": hour, "minute": minute}
        )

    async def async_lock_ha(self) -> dict[str, Any]:
        """POST /api/lock — indefinite HA lock, removable only via DELETE /api/lock."""
        return await self._api_wrapper("POST", "/api/lock", data={"mode": "ha"})

    async def async_unlock(self) -> dict[str, Any]:
        """DELETE /api/lock — cancel any active lock including HA lock."""
        return await self._api_wrapper("DELETE", "/api/lock")

    # ── Restore ───────────────────────────────────────────────────────────────

    async def async_toggle_restore(self, enabled: bool) -> dict[str, Any]:
        """POST /api/restore — enable or disable auto-restore of blocked apps."""
        return await self._api_wrapper("POST", "/api/restore", data={"enabled": enabled})
