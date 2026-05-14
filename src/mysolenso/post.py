"""Generic HTTP POST module for MySolenso requests.

Provides the :class:`MySolensoPost` class, a lightweight and configurable
HTTP client that wraps a :mod:`requests` session with header management,
JSON payload handling, and response validation.

This module is used internally by the services
(:mod:`mysolenso.services.me` and :mod:`mysolenso.services.station`)
to avoid code duplication.

Example:
    Typical usage inside a service::

        from mysolenso.post import MySolensoPost

        client = MySolensoPost(timeout=15)
        client.set_headers({"Cookie": "solenso_token=..."})
        data = client.post("https://monitor.solenso.net/api/...")
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from .exceptions import (
    MySolensoException,
    MySolensoAuthenticationException,
)
from .const import DEFAULT_TIMEOUT

_LOG = logging.getLogger(__name__)


class MySolensoPost:
    """HTTP POST client with header management and JSON response validation.

    Wraps a persistent :class:`requests.Session` and provides methods to
    configure headers, define a default JSON payload, and execute POST
    requests with automatic validation of the Solenso API response
    (``status`` and ``message`` fields).

    Args:
        timeout (int): Request timeout in seconds.
            Defaults to :data:`~mysolenso.const.DEFAULT_TIMEOUT` (10 s).

    Attributes:
        timeout (int): Configured request timeout.

    Example:
        ::

            client = MySolensoPost()
            client.set_header("Cookie", "solenso_token=tok123")
            result = client.post("https://monitor.solenso.net/api/endpoint")
            print(result)  # dict from the data{} field
    """

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout

        # Default headers accepted by the Solenso API
        self._headers: Dict[str, str] = {
            "User-Agent": "MySolenso/1.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        }

        # Default JSON payload used when none is passed to post()
        self._raw_payload: Dict[str, Any] = {}

        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def headers(self) -> Dict[str, str]:
        """Current HTTP headers of the session.

        Returns:
            Dict[str, str]: Current headers dictionary.
        """
        return self._headers

    @property
    def raw_payload(self) -> Dict[str, Any]:
        """Default JSON payload used when :meth:`post` receives no payload.

        Returns:
            Dict[str, Any]: Current default payload.
        """
        return self._raw_payload

    # ------------------------------------------------------------------
    # Header management
    # ------------------------------------------------------------------

    def set_header(self, key: str, value: str) -> None:
        """Add or replace a single HTTP header.

        Args:
            key (str): Header name (e.g. ``"Authorization"``).
            value (str): Header value.

        Example:
            ::

                client.set_header("X-Custom", "value")
        """
        self._headers[key] = value

    def remove_header(self, key: str) -> None:
        """Remove an HTTP header if it exists.

        No exception is raised if the key is absent.

        Args:
            key (str): Header name to remove.
        """
        if key in self._headers:
            del self._headers[key]

    def set_headers(self, headers: Dict[str, str]) -> None:
        """Merge a dictionary of headers into the existing headers.

        Existing keys are overwritten; new keys are added.

        Args:
            headers (Dict[str, str]): Headers to merge.

        Example:
            ::

                client.set_headers(auth.get_auth_headers_solenso())
        """
        self._headers.update(headers)

    # ------------------------------------------------------------------
    # Payload management
    # ------------------------------------------------------------------

    def set_raw_payload(self, payload: Dict[str, Any]) -> None:
        """Set the default JSON payload sent by :meth:`post`.

        Args:
            payload (Dict[str, Any]): JSON body to store. Must be a
                dictionary.

        Raises:
            MySolensoException: If ``payload`` is not a dictionary.
        """
        if not isinstance(payload, dict):
            raise MySolensoException("Payload must be a dictionary.")
        self._raw_payload = payload

    # ------------------------------------------------------------------
    # HTTP request
    # ------------------------------------------------------------------

    def post(
        self,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Perform a JSON POST request and return the validated data.

        Sends ``payload`` (or :attr:`raw_payload` if ``None``) to ``url``,
        checks the HTTP status, validates the Solenso API response structure
        (``status == "0"`` and ``message == "success"``), then returns only
        the content of the ``data`` field.

        Args:
            url (str): Target URL for the POST request.
            payload (Optional[Dict[str, Any]]): JSON payload to send.
                If ``None``, :attr:`raw_payload` is used.

        Returns:
            dict: Content of the ``data`` field from the JSON response.

        Raises:
            MySolensoAuthenticationException: If the response ``status``
                field is not ``"0"`` or ``message`` is not ``"success"``.
            MySolensoException: On timeout, HTTP error, or invalid JSON
                response.

        Example:
            ::

                client = MySolensoPost()
                client.set_headers(auth.get_auth_headers_solenso())
                data = client.post(API_USER_ME)
                print(data["user_name"])
        """
        final_payload = payload if payload is not None else self._raw_payload

        try:
            response = self._session.post(
                url,
                headers=self._headers,
                json=final_payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._safe_json(response)

        except Timeout as exc:
            raise MySolensoException("HTTP request timeout.") from exc

        except RequestException as exc:
            raise MySolensoException(f"HTTP request error: {exc}") from exc
        
    def poststr(
        self,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bytes:

        final_payload = payload if payload is not None else self._raw_payload

        try:
            response = self._session.post(
                url,
                headers=self._headers,
                json=final_payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.content

        except Timeout as exc:
            raise MySolensoException("HTTP request timeout.") from exc

        except RequestException as exc:
            raise MySolensoException(f"HTTP request error: {exc}") from exc

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_json(response: Response) -> dict:
        """Parse and validate the Solenso API JSON response.

        Verifies that the response is a valid dict, that ``status`` equals
        ``"0"`` and ``message`` equals ``"success"``, then returns only the
        content of ``data``.

        Args:
            response (Response): HTTP response to process.

        Returns:
            dict: Content of the ``data`` field (may be empty if absent).

        Raises:
            MySolensoAuthenticationException: If ``status != "0"`` or
                ``message != "success"``.
            MySolensoException: If the JSON is invalid or not a dict.
        """
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError

            # Strict validation of the Solenso API contract
            status = str(data.get("status", "")).strip()
            message = str(data.get("message", "")).strip().lower()

            if status != "0":
                raise MySolensoAuthenticationException(
                    f"API error - status={status}, message={data.get('message')}"
                )

            if message != "success":
                raise MySolensoAuthenticationException(
                    f"Authentication failed - message={data.get('message')}"
                )

            return data.get("data", {})

        except ValueError as exc:
            raise MySolensoException("Invalid JSON response.") from exc

    def __repr__(self) -> str:
        """Text representation of the HTTP client.

        Returns:
            str: String listing the timeout and the present header keys.
        """
        return (
            f"{self.__class__.__name__}("
            f"timeout={self.timeout}, "
            f"headers={list(self._headers.keys())})"
        )
