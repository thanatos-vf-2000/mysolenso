"""MySolenso user profile service.

Provides the :class:`MySolensoMe` class, which queries the
``/fun_api_1_user_me`` endpoint and exposes the connected account's
information as Python properties.

This module is instantiated automatically by :class:`~mysolenso.MySolenso`
and accessible via ``client.me``.

Example:
    ::

        client = MySolenso(username="jdoe", token="tok")
        print(client.me.name)
        print(client.me.email)
        print(client.me.group_name)
"""

from __future__ import annotations

import logging
from ..post import MySolensoPost
from ..const import API_USER_ME
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoMe:
    """Access to the connected Solenso user account information.

    Queries the API once at instantiation and caches the profile data.
    Properties are then available without any additional network call.

    Args:
        parent: Instance of :class:`~mysolenso.MySolenso` providing
            access to the ``auth`` sub-module (for session headers).

    Raises:
        MySolensoException: If the API response is invalid or if a network
            error occurs during initialisation.

    Attributes:
        parent: Reference to the parent :class:`~mysolenso.MySolenso` object.

    Example:
        ::

            client = MySolenso(username="jdoe", token="tok")
            me = client.me

            print(me.username)    # "jdoe"
            print(me.name)        # "John DOE"
            print(me.email)       # "jdoe@jdoe.com"
            print(me.phone)       # "+33600000000"
            print(me.role_ids)    # "1"
            print(me.roles_name)  # "Administrator"
            print(me.group_name)  # "Install Solenso"
            print(me.all_data)    # full dict returned by the API 
    """

    def __init__(self, parent) -> None:
        self.parent = parent
        self._get_user_me()

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_user_me(self) -> None:
        """Query the API to retrieve the connected user's profile.

        Creates a :class:`~mysolenso.post.MySolensoPost` client, injects
        the Solenso session headers, and maps the JSON response fields onto
        the instance's private attributes.

        Raises:
            MySolensoException: If the request fails or the response is
                malformed.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            response = self._client.post(API_USER_ME)

            # Extract and normalise profile fields
            self._username   = str(response.get("user_name", "")).strip()
            self._name       = str(response.get("name", "")).strip()
            self._phone      = str(response.get("phone", "")).strip()
            self._email      = str(response.get("email", "")).strip()
            self._role_ids   = str(response.get("role_ids", "")).strip()
            # First role from the list (format: [{"name": "..."}])
            self._roles_name = str(
                response.get("roles", [{}])[0].get("name", "")
            ).strip()
            # User group name (format: {"name": "..."})
            self._group_name = str(
                response.get("group", {}).get("name", "")
            ).strip()
            self._all_data = response

        except Exception as e:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from e

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def username(self) -> str:
        """Login identifier (email address or username).

        Returns:
            str: Value of the ``user_name`` field returned by the API.
        """
        return self._username

    @property
    def name(self) -> str:
        """Full name of the user.

        Returns:
            str: Value of the ``name`` field returned by the API.
        """
        return self._name

    @property
    def phone(self) -> str:
        """Phone number associated with the account.

        Returns:
            str: Value of the ``phone`` field returned by the API, or an
            empty string if not set.
        """
        return self._phone

    @property
    def email(self) -> str:
        """Email address of the account.

        Returns:
            str: Value of the ``email`` field returned by the API.
        """
        return self._email

    @property
    def role_ids(self) -> str:
        """Raw role identifier(s) assigned to the user.

        Returns:
            str: Value of the ``role_ids`` field returned by the API.
        """
        return self._role_ids

    @property
    def roles_name(self) -> str:
        """Name of the first role assigned to the user.

        Returns:
            str: Value of the ``name`` field from the first element of
            ``roles``.
        """
        return self._roles_name

    @property
    def group_name(self) -> str:
        """Name of the group the user belongs to.

        Returns:
            str: Value of the ``name`` field from the ``group`` object.
        """
        return self._group_name

    @property
    def all_data(self) -> dict:
        """Full raw data returned by the API.

        Useful for accessing fields not exposed by the other properties.
        
        Example:
            {
                "id": 123456,
                "user_name": "JDOE",
                "type": 3,
                "gid": 234567,
                "name": "John Doe",
                "phone": "+33600000000",
                "email": "jdoe@jdoe.com",
                "role_ids": [90],
                "identity": 0,
                "src": 0,
                "tid": 197,
                "gpath": "100267.100269.111139.136448",
                "dc": 0,
                "roles": [
                    {
                        "name": "Propriétaire",
                        "id": 90,
                        "v": 0
                    }
                ],
                "group": {
                    "id": 987654,
                    "name": "Install Solenso",
                    "type": 4
                },
                "services": [
                    {
                        "gdpr": 0
                    }
                ]
            }

        Returns:
            dict: Complete dictionary from the ``data`` field of the response.
        """
        return self._all_data
