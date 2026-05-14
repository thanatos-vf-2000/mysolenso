"""Configuration constants for the MySolenso library.

This module centralises all fixed values used by the library:
base URL, API endpoints, and network parameters. Modifying this file
is sufficient to point the library at a different environment (e.g. staging).

Attributes:
    DEFAULT_TIMEOUT (int): Network timeout in seconds applied to every HTTP
        request. Defaults to ``10``.
    BASE_URL_SOLENSO (str): Root URL of the Solenso platform.
        All API routes are built from this base.
    API_AUTH_LOGIN (str): Authentication endpoint. Expects a JSON payload
        containing ``user_name`` and ``password``, and returns a session token.
    API_USER_ME (str): Authenticated user profile endpoint. Returns account
        information (name, email, role, group…).
    API_STATION_ME (str): User PV station list endpoint. Returns a paginated
        response with ``total`` and ``list``.
    API_STATION_FIND (str): station data list endpoint. Returns a paginated
        response with all data.

Example:
    Direct use of constants (internal usage)::

        from mysolenso.const import API_AUTH_LOGIN, DEFAULT_TIMEOUT
        response = session.post(API_AUTH_LOGIN, json=payload, timeout=DEFAULT_TIMEOUT)
"""

DEFAULT_TIMEOUT: int = 10
"""Network timeout in seconds (default: ``10``)."""

BASE_URL_SOLENSO: str = "https://monitor.solenso.net/platform/"
"""Root URL of the Solenso monitoring platform."""

# --- Authentication endpoints ---

API_AUTH_LOGIN: str = BASE_URL_SOLENSO + "api/gateway/iam/auth_login"
"""POST endpoint for credential-based authentication."""

# --- User endpoints ---

API_USER_ME: str = BASE_URL_SOLENSO + "api/gateway/iam/fun_api_1_user_me"
"""GET endpoint for the connected user account information."""

# --- Station endpoints ---

API_STATION_ME: str = BASE_URL_SOLENSO + "api/gateway/pvm/station_select_by_page"
"""POST endpoint for paginated retrieval of the user's PV stations."""

API_STATION_FIND: str = BASE_URL_SOLENSO + "api/gateway/pvm/station_find"
"""POST endpoint to retrieve the full detail record of a single PV station."""
