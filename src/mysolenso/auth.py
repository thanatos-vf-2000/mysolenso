"""MySolenso authentication module.

Provides the :class:`MySolensoAuth` class, which manages the HTTP session,
authentication via password or token, and generation of authorisation headers
for the two underlying APIs (Solenso and Hoymiles).

Source: https://github.com/thanatos-vf-2000/mysolenso

Example:
    Connect with a password (the token is retrieved automatically)::

        from mysolenso.auth import MySolensoAuth

        auth = MySolensoAuth(username="jdoe", password="encrypted_pass")
        print(auth.isConnect())                   # True
        print(auth.token)                         # "eyJ..."
        print(auth.get_auth_headers_solenso())

    Connect directly with an existing token::

        auth = MySolensoAuth(username="jdoe", token="eyJ...")
        headers = auth.get_auth_headers_hoymiles()
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from .exceptions import (
    MySolensoException,
    MySolensoConnectionException,
    MySolensoAuthenticationException,
)
from .const import (
    DEFAULT_TIMEOUT,
    API_AUTH_LOGIN,
)

_LOG = logging.getLogger(__name__)


class MySolensoAuth:
    """Secure and robust HTTP client for the Solenso API.

    Handles authentication (via encrypted password or a pre-existing token),
    maintains the HTTP session with the correct headers, and exposes the
    helper methods required by other library modules.

    The class is thread-safe: token reads and writes are protected by an
    internal :class:`threading.Lock`.

    Args:
        username (str): Email address or account identifier on Solenso.
            Must not be empty or blank.
        password (Optional[str]): **Encrypted** password as sent by the
            Solenso web interface. Triggers a call to :meth:`_authenticate`
            when provided.
        token (Optional[str]): Existing session token. Used as-is without
            any additional network call.

    Raises:
        MySolensoConnectionException: If ``username`` is empty, or if neither
            ``password`` nor ``token`` is provided.
        MySolensoAuthenticationException: If the API returns an error status
            or a missing token during password-based authentication.
        MySolensoException: On timeout or network error during authentication.

    Attributes:
        username (str): Account identifier (whitespace-stripped).

    Example:
        ::

            auth = MySolensoAuth(username="jdoe", token="tok_abc123")
            if auth.isConnect():
                headers = auth.get_auth_headers_solenso()
    """

    def __init__(
        self,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        if not username or not username.strip():
            raise MySolensoConnectionException("The 'username' field is required.")

        if password is None and token is None:
            raise MySolensoConnectionException(
                "You must provide either an encrypted password or a token."
            )

        self.username = username.strip()
        self._token = token.strip() if token else ""
        self._token_language = "fr_fr"

        # Lock for concurrent access to the token
        self._lock = threading.Lock()

        # Shared HTTP session (persistent connections, connection pool)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "MySolenso/1.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        })

        # Automatic authentication if a password is provided
        if password:
            self._authenticate(password)

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def token(self) -> str:
        """Current session token.

        Returns:
            str: JWT/opaque token returned by the API, or an empty string
            if not authenticated.
        """
        return self._token

    @property
    def token_language(self) -> str:
        """Language code sent in the session cookie.

        Returns:
            str: Language code in ``ll_LL`` format (e.g. ``"fr_fr"``).
        """
        return self._token_language

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def isConnect(self) -> bool:
        """Check whether a valid session token is present in memory.

        Returns:
            bool: ``True`` if the token is non-empty, ``False`` otherwise.

        Example:
            ::

                auth = MySolensoAuth(username="jdoe", token="tok_abc123")
                assert auth.isConnect() is True
                auth.disconnect()
                assert auth.isConnect() is False
        """
        return bool(self._token and self._token.strip())

    def get_auth_headers_solenso(self) -> dict:
        """Build the ``Cookie`` headers for the Solenso API.

        Calls to the Solenso API (profile, stations…) authenticate via two
        cookies: ``solenso_token_language`` and ``solenso_token``.

        Returns:
            dict: Dictionary containing the ``"Cookie"`` key with the
            formatted value.

        Raises:
            MySolensoAuthenticationException: If no valid token is available
                (disconnected session).

        Example:
            ::

                headers = auth.get_auth_headers_solenso()
                # {"Cookie": "solenso_token_language=fr_fr; solenso_token=eyJ..."}
        """
        if not self.isConnect():
            raise MySolensoAuthenticationException("No tokens available.")

        return {
            "Cookie": (
                f"solenso_token_language={self._token_language}; "
                f"solenso_token={self._token}"
            )
        }

    def get_auth_headers_hoymiles(self) -> dict:
        """Build the ``Authorization`` headers for the Hoymiles API.

        Hoymiles micro-inverters used by Solenso require an
        ``Authorization: Bearer <token>`` header.

        Returns:
            dict: Dictionary containing the ``"Authorization"`` key with
            the ``Bearer`` scheme.

        Raises:
            MySolensoAuthenticationException: If no valid token is available.

        Example:
            ::

                headers = auth.get_auth_headers_hoymiles()
                # {"Authorization": "Bearer eyJ..."}
        """
        if not self.isConnect():
            raise MySolensoAuthenticationException("No tokens available.")

        return {"Authorization": f"{self._token}"}

    def disconnect(self) -> None:
        """Remove the session token from memory.

        After this call, :meth:`isConnect` returns ``False`` and any call
        to ``get_auth_headers_*`` methods will raise an exception.

        Note:
            This method does not revoke the token server-side on Solenso;
            it only clears the local token.
        """
        with self._lock:
            self._token = ""

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _authenticate(self, password: str) -> None:
        """Send credentials to the API and store the returned token.

        Builds a RAW payload in the format expected by the Solenso API,
        strictly validates the response (status ``"0"``, message
        ``"success"``), then stores the token in a thread-safe manner.

        Args:
            password (str): Encrypted password as sent by the browser
                when logging in on monitor.solenso.net.

        Raises:
            MySolensoAuthenticationException: If the API status differs from
                ``"0"``, if the message is not ``"success"``, or if the token
                is absent from the ``data`` field of the response.
            MySolensoException: On network timeout or HTTP error.
        """
        raw_payload = {
            "ERROR_BACK": True,
            "LOAD": {"loading": True},
            "body": {
                "user_name": self.username,
                "password": password,
            },
            "WAITING_PROMISE": True,
        }

        try:
            response = self._post(API_AUTH_LOGIN, json=raw_payload)
            data = self._safe_json(response)

            # Strict validation of the API response
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

            token = data.get("data", {}).get("token", "").strip()

            if not token:
                raise MySolensoAuthenticationException(
                    "Token missing from the API response."
                )

            with self._lock:
                self._token = token

        except Timeout as exc:
            raise MySolensoException("Timeout during authentication.") from exc

        except RequestException as exc:
            raise MySolensoException(f"Network/API error: {exc}") from exc

    def _post(self, url: str, **kwargs) -> Response:
        """Perform a POST request with a forced timeout.

        Delegates to the shared HTTP session, ensuring a timeout is always
        set, then checks the HTTP status code via ``raise_for_status``.

        Args:
            url (str): Target URL for the request.
            **kwargs: Additional arguments passed to
                :meth:`requests.Session.post` (e.g. ``json``, ``headers``).

        Returns:
            Response: Requests response object if the HTTP status is 2xx.

        Raises:
            requests.HTTPError: If the HTTP status is 4xx or 5xx.
            requests.Timeout: If the :data:`~mysolenso.const.DEFAULT_TIMEOUT`
                is exceeded.
        """
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        response = self._session.post(url, **kwargs)
        response.raise_for_status()
        return response

    @staticmethod
    def _safe_json(response: Response) -> dict:
        """Safely parse the HTTP response as JSON.

        Args:
            response (Response): Requests response object to deserialise.

        Returns:
            dict: Deserialised JSON body.

        Raises:
            MySolensoException: If the body is not valid JSON or is not a
                dictionary.
        """
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Invalid JSON response.")
            return data
        except ValueError as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

    def __repr__(self) -> str:
        """Text representation without exposing the token.

        Returns:
            str: String of the form
            ``MySolensoAuth(username='…', isConnected=True/False)``.
        """
        return (
            f"{self.__class__.__name__}("
            f"username='{self.username}', "
            f"isConnected={self.isConnect()})"
        )
