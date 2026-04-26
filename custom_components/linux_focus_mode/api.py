"""API Client for the Focus Mode integration.

This module provides the asynchronous client used to communicate with the local Focus Mode
FastAPI backend. It strictly adheres to Home Assistant's non-blocking requirements by
utilizing `aiohttp` and `async_timeout`.
"""

from __future__ import annotations

import asyncio
import socket
from typing import Any

import aiohttp
import async_timeout


class FocusModeApiError(Exception):
    """Base exception for all Focus Mode API errors.

    Used to catch any generic or unexpected errors that occur during API communication,
    ensuring that the Home Assistant core does not crash due to unhandled exceptions
    from this integration.
    """


class FocusModeApiCommunicationError(FocusModeApiError):
    """Exception raised when a network communication error occurs.

    This includes connection timeouts, TCP/IP level socket errors, and DNS resolution
    failures, indicating that the backend is unreachable.
    """


class FocusModeApiAuthenticationError(FocusModeApiError):
    """Exception raised when the provided authentication token is invalid.

    Triggered when the backend returns HTTP 401 Unauthorized or HTTP 403 Forbidden.
    """


class FocusModeApiClient:
    """Asynchronous client for interacting with the Focus Mode API.

    This client abstracts the underlying HTTP details and provides clear, typed methods
    for fetching the current state and toggling the focus mode.
    """

    def __init__(self, host: str, token: str, session: aiohttp.ClientSession) -> None:
        """Initialize the Focus Mode API Client.

        Args:
            host: The base URL of the Focus Mode FastAPI server (e.g., "http://192.168.1.100:8000").
            token: The 32-character Bearer token used for authorization.
            session: The `aiohttp.ClientSession` provided by Home Assistant (`async_get_clientsession`),
                which ensures connection pooling and avoids creating unnecessary new sessions.
        """
        self._host = host.rstrip("/")
        self._token = token
        self._session = session

    async def _api_wrapper(
        self, method: str, url: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Wrap the underlying async HTTP requests to the Focus Mode API.

        This internal method centralizes error handling, timeout enforcement, and
        JSON parsing for all API endpoints, reducing code duplication.

        Args:
            method: The HTTP method to use (e.g., "GET", "POST").
            url: The relative URL path for the API endpoint.
            data: Optional JSON payload to include in the request body.

        Returns:
            A dictionary containing the JSON response from the backend.

        Raises:
            FocusModeApiAuthenticationError: If the server rejects the request due to invalid credentials.
            FocusModeApiCommunicationError: If the server cannot be reached or the request times out.
            FocusModeApiError: If an unexpected error occurs during parsing or communication.
        """
        headers = {"Authorization": f"Bearer {self._token}"}

        try:
            # We enforce a strict timeout of 10 seconds. In the context of Home Assistant,
            # we cannot allow a blocked or infinitely hanging network call to tie up the
            # async event loop, which would degrade the performance of the entire smart home system.
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=f"{self._host}{url}",
                    headers=headers,
                    json=data,
                )

                # Differentiate authentication errors from generic HTTP errors so the Config Flow
                # can prompt the user specifically to re-authenticate if necessary.
                if response.status in (401, 403):
                    raise FocusModeApiAuthenticationError("Invalid credentials")

                # Raise an aiohttp.ClientResponseError for any other non-2xx status codes.
                response.raise_for_status()
                return await response.json()

        except asyncio.TimeoutError as exception:
            raise FocusModeApiCommunicationError(
                "Timeout occurred while connecting to API"
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            # socket.gaierror catches DNS resolution failures, while aiohttp.ClientError
            # covers connection refusals and reset exceptions.
            raise FocusModeApiCommunicationError(
                "Error occurred while communicating with API"
            ) from exception
        except FocusModeApiAuthenticationError:
            # Re-raise authentication errors directly so they aren't caught by the generic block below.
            raise
        except Exception as exception:  # pylint: disable=broad-except
            # Fallback for any other obscure errors (e.g., malformed JSON parsing issues)
            # to guarantee that only our custom exception types leak out of this wrapper.
            raise FocusModeApiError(
                f"Something really wrong happened! - {exception}"
            ) from exception

    async def async_get_state(self) -> dict[str, Any]:
        """Fetch the current operational state from the API.

        This endpoint is polled by the DataUpdateCoordinator to keep Home Assistant
        in sync with external changes to the Focus Mode backend.

        Returns:
            A dictionary representing the state:
            `{"active": bool, "blocked_items": list[dict], "focus_lock": dict}`

        Raises:
            FocusModeApiAuthenticationError: If the token is invalid.
            FocusModeApiCommunicationError: If the connection fails or times out.
        """
        return await self._api_wrapper("GET", "/api/state")

    async def async_toggle_blocker(self, active: bool) -> dict[str, Any]:
        """Toggle the Focus Mode blocker on or off.

        Args:
            active: True to enable Focus Mode blocking, False to disable it.

        Returns:
            A dictionary mirroring the updated state from the server.

        Raises:
            FocusModeApiAuthenticationError: If the token is invalid.
            FocusModeApiCommunicationError: If the connection fails or times out.
        """
        return await self._api_wrapper("POST", "/api/toggle", data={"active": active})
