"""Main entry point for the MySolenso library.

This module exposes the :class:`MySolenso` facade class, which groups the
three library sub-modules:

- :attr:`MySolenso.auth` — session management and token handling
- :attr:`MySolenso.me` — user account information
- :attr:`MySolenso.station` — photovoltaic station data

This is the only class that most users need to import.

Example:
    Connect with an encrypted password::

        from mysolenso import MySolenso

        client = MySolenso(username="jdoe", password="encrypted_pass")

        # Authentication
        print(client.auth.isConnect())   # True
        print(client.auth.token)

        # User profile
        print(client.me.name)
        print(client.me.email)

        # Active station
        print(client.station.station_id)
        print(client.station.install_power)

    Connect directly with an existing token (avoids the authentication
    network call)::

        client = MySolenso(username="jdoe", token="eyJ...")
"""

from __future__ import annotations

import logging
from typing import Optional

from .auth import MySolensoAuth
from .services.me import MySolensoMe
from .services.station import MySolensoStation

_LOG = logging.getLogger(__name__)


class MySolenso:
    """Main facade for the MySolenso library.

    Instantiates and groups the three sub-modules (``auth``, ``me``,
    ``station``) into a unified interface. Authentication and initial data
    loading (profile + stations) are performed automatically at construction.

    Args:
        username (str): Email address or Solenso account identifier.
        password (Optional[str]): Encrypted password. If provided, a network
            call is made to obtain the session token.
        token (Optional[str]): Existing session token. If provided, no
            additional authentication call is made.

    Raises:
        MySolensoConnectionException: If ``username`` is empty or if neither
            ``password`` nor ``token`` is provided.
        MySolensoAuthenticationException: If the credentials are invalid.
        MySolensoException: On network error or missing data during
            sub-module initialisation.

    Attributes:
        username (str): Account identifier.
        password (Optional[str]): Password kept in memory; not reused after
            construction.
        token (Optional[str]): Initial token provided at construction.
        auth (MySolensoAuth): Sub-module for session management and
            authorisation headers.
        me (MySolensoMe): Sub-module for user profile access.
        station (MySolensoStation): Sub-module for PV station access.

    Example:
        ::

            from mysolenso import MySolenso
            from mysolenso.exceptions import MySolensoException

            try:
                client = MySolenso(username="admin", password="encrypted_pass")
                print(client.me.name)
                print(client.station.station_total)
            except MySolensoException as e:
                print(f"Error: {e}")
    """

    def __init__(
        self,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        self.username = username
        self.password = password
        self.token = token

        # --- Sequential initialisation of sub-modules ---

        # 1. Authentication (raises an exception if credentials are invalid)
        self.auth = MySolensoAuth(
            username=self.username,
            password=self.password,
            token=self.token,
        )

        # 2. User profile (requires a valid token)
        self.me = MySolensoMe(self)

        # 3. PV stations (requires a valid token; raises if no station found)
        self.station = MySolensoStation(self)
