"""Service for retrieving the geographic and address data of a station.

This module provides :class:`MySolensoStationAK`, which wraps the
``station_ak_find`` Solenso endpoint. One call returns the station's
latitude, longitude, and human-readable address.

Typical usage::

    client = MySolenso(username="user@example.com", password="...")
    client.stationak.station_ak_refresh()
    print(client.stationak.address)
    print(client.stationak.latitude, client.stationak.longitude)
"""

from __future__ import annotations

import logging
from typing import Any

from ...post import MySolensoPost
from ...const import API_STATION_AK
from ...exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoStationAK:
    """Retrieve geographic and address information for the active station.

    This service queries the ``station_ak_find`` endpoint using the station ID
    and its associated AK (access key) string. Call
    :meth:`station_ak_refresh` to populate the data, then read the properties
    :attr:`longitude`, :attr:`latitude`, and :attr:`address`.

    Use :meth:`set_station` to switch to a different station without
    rebuilding the entire client.

    Args:
        parent (MySolenso): The parent client object that holds the
            authentication context and the active station reference.

    Raises:
        MySolensoException: If no active station is set on the parent at
            construction time (``parent.station.station_id is None``).

    Example::

        client = MySolenso(username="user@example.com", token="...")
        client.stationak.station_ak_refresh()
        print(client.stationak.address)
        # → "95 Moon Road, 99999 Galaxy, World"
    """

    def __init__(self, parent) -> None:
        # Keep a reference to the parent client for auth and station access.
        self.parent = parent

        # Validate that a station has already been selected by the parent.
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        # Cache the current station ID and AK from the parent.
        self._station_id = self.parent.station.station_id
        self._station_ak = self.parent.station.ak

        # Placeholders - populated by _get_station_ak().
        self._all_data: dict = {}
        self._id: int | None = None
        self._longitude: str | None = None
        self._latitude: str | None = None
        self._address: str | None = None

    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------

    def set_station(self, id: int, ak: str, refresh: bool = True) -> None:
        """Switch the active station for geographic data queries.

        Updates the cached station ID and AK, then optionally re-fetches
        the data.  The station must exist in the account's station list.

        Args:
            id (int): Internal numeric ID of the target station.
            ak (str): The station's AK (access key / identifier) string,
                available as ``client.station.ak``.
            refresh (bool): When ``True`` (default), immediately re-fetches
                the geographic data for the new station.  Set to ``False``
                to defer the network call.

        Raises:
            MySolensoException: If the requested station ID is not found in
                the account's station list.

        Example::

            client.stationak.set_station(id=9999999, ak="abc123")
            print(client.stationak.address)
        """
        stations = self.parent.station.stations

        # Verify the requested station ID exists in the account.
        if not any(station.get("id") == id for station in stations):
            msg = (
                f"{self.__class__.__name__} - set_station: "
                f"station {id} not found."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = id
        self._station_ak = ak

        # Reload data for the new station unless the caller deferred it.
        if refresh:
            self._get_station_ak()

    # ------------------------------------------------------------------
    # Data retrieval (internal)
    # ------------------------------------------------------------------

    def _get_station_ak(self) -> None:
        """Fetch geographic data from the ``station_ak_find`` endpoint.

        Builds the POST request body, sends it, parses the response, and
        stores both the raw dictionary and the individual cleaned fields
        as private instance attributes.

        Raises:
            MySolensoException: If the API returns an empty response or if
                the JSON payload cannot be parsed.
        """
        try:
            # Initialise a new HTTP POST client and attach auth headers.
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())

            # Build the request body with the station ID and its AK.
            self._client.set_raw_payload({
                "ERROR_BACK": True,
                "body": {
                    "sid": self._station_id,
                    "ak": self._station_ak,
                },
                "WAITING_PROMISE": True,
            })

            response = self._client.post(API_STATION_AK)

            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_station_ak: "
                    f"response data not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            # Store the complete raw response dictionary.
            self._all_data = response

            # ----------------------------------------------------------
            # Helper: recursively strip strings; pass-through other types.
            # ----------------------------------------------------------
            def _clean(
                value: str | int | float | bool | list | dict | None,
            ) -> str | int | float | bool | list | dict | None:
                """Strip whitespace from strings; recurse into lists/dicts.

                Args:
                    value: Any Python scalar, list, or dict from the JSON
                        response.

                Returns:
                    The cleaned value with the same type as the input.
                """
                if value is None:
                    return None
                if isinstance(value, str):
                    return value.strip()
                if isinstance(value, list):
                    return [_clean(item) for item in value]
                if isinstance(value, dict):
                    return {_clean(k): _clean(v) for k, v in value.items()}
                return value

            # Extract and clean the individual geographic fields.
            self._id        = _clean(self._all_data.get("id"))
            self._longitude = _clean(self._all_data.get("longitude"))
            self._latitude  = _clean(self._all_data.get("latitude"))
            self._address   = _clean(self._all_data.get("address"))

        except MySolensoException:
            # Re-raise known library exceptions without wrapping.
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def station_ak_refresh(self) -> None:
        """Force a fresh fetch of the station geographic data from the API.

        Delegates to :meth:`_get_station_ak`.  Call this method any time
        you need up-to-date coordinates or address information.

        Example::

            client.stationak.station_ak_refresh()
            print(client.stationak.longitude)
        """
        self._get_station_ak()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        """Raw API response for the ``station_ak_find`` endpoint.

        Returns:
            dict: Station geographic record returned verbatim by the API.
            Example::

                {
                    "id": 9999999,
                    "longitude": "39.10884652257048",
                    "latitude": "-76.77128918829347",
                    "address": "95 Moon Road, 99999 Galaxy, World"
                }

        Raises:
            AttributeError: If :meth:`station_ak_refresh` has not been
                called yet.
        """
        return self._all_data

    @property
    def id(self) -> int:
        """Internal numeric ID of the station.

        Returns:
            int: The station identifier as stored on the Solenso platform.
        """
        return self._id

    @property
    def longitude(self) -> str:
        """Longitude of the station as a decimal-degree string.

        Returns:
            str: Decimal-degree longitude (positive = East, negative = West).
            Example: ``"39.10884652257048"``.
        """
        return self._longitude

    @property
    def latitude(self) -> str:
        """Latitude of the station as a decimal-degree string.

        Returns:
            str: Decimal-degree latitude (positive = North, negative = South).
            Example: ``"-76.77128918829347"``.
        """
        return self._latitude

    @property
    def address(self) -> str:
        """Human-readable postal address of the station.

        Returns:
            str: Full address string as entered on the Solenso platform.
            Example: ``"95 Moon Road, 99999 Galaxy, World"``.
        """
        return self._address
