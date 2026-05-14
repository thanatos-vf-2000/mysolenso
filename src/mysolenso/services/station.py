"""MySolenso PV station service.

Provides the :class:`MySolensoStation` class, which queries the
``/station_select_by_page`` endpoint and exposes the user's photovoltaic
installation data.

When an account has multiple stations, the class selects the first one by
default. Use :meth:`MySolensoStation.set_station` to switch the active station.

This module is instantiated automatically by :class:`~mysolenso.MySolenso`
and accessible via ``client.station``.

Example:
    ::

        client = MySolenso(username="user", token="tok")

        print(client.station.station_total)   # total number of stations
        print(client.station.station_id)      # ID of the active station
        print(client.station.name)            # installation name
        print(client.station.install_power)   # installed power
        print(client.station.stations)        # list of [{id, ak}, ...]
"""

from __future__ import annotations

import logging
from typing import Union, List

from ..post import MySolensoPost
from ..const import API_STATION_ME
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoStation:
    """Access to the Solenso user's photovoltaic stations.

    Queries the API at instantiation to retrieve the complete list of
    stations. The active station index (1-based) can be changed with
    :meth:`set_station`.

    Args:
        parent: Instance of :class:`~mysolenso.MySolenso` providing
            access to the ``auth`` sub-module.

    Raises:
        MySolensoException: If no station is found (``total == 0``), or if
            the API response is invalid.

    Note:
        The station index is **1-based**: the first station is
        ``station = 1``, the second is ``station = 2``, and so on.

    Example:
        ::

            client = MySolenso(username="admin", token="tok")
            st = client.station

            print(st.station_total)   # 2
            print(st.station_id)      # ID of station 1
            st.set_station(2)         # switch to station 2
            print(st.station_id)      # ID of station 2
    """

    def __init__(self, parent) -> None:
        self.parent = parent

        # Initialise attributes before the first refresh
        self._station_id    = None
        self._name          = None
        self._city_code     = None
        self._status        = None
        self._create_at     = None
        self._tz_name       = None
        self._capacitor     = None
        self._install_power = None
        self._address       = None
        self._org_name      = None
        self._warn_data     = None
        self._ak            = None

        # Fetch the station list (sets total and all_data)
        self._get_station_me()

        # Load the details of the active station (index 1 by default)
        self.refresh_station()

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_station_me(self) -> None:
        """Query the API and store the complete station list.

        Performs a POST to :data:`~mysolenso.const.API_STATION_ME`,
        extracts ``total`` (number of stations) and ``list`` (raw data),
        then sets the current index to ``1`` (first station).

        Raises:
            MySolensoException: If the request fails, the response is
                malformed, or no station is available.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            response = self._client.post(API_STATION_ME)

            self._total    = int(response.get("total", 0))
            self._all_data = response.get("list", {})
            self._station  = 1  # 1-based index, points to the first station

        except Exception as e:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from e

        if self._total == 0:
            self._station = 0
            _LOG.warning("%s - MySolensoStation no data.", self.__class__.__name__)
            raise MySolensoException("MySolensoStation no data.")

    # ------------------------------------------------------------------
    # Station selection and refresh
    # ------------------------------------------------------------------

    def set_station(self, id: int) -> None:
        """Select the active station by its 1-based index.

        Args:
            id (int): Index of the station to activate. Must be between
                ``1`` and :attr:`station_total` inclusive.

        Raises:
            MySolensoException: If ``id`` is out of the valid range.

        Example:
            ::

                client.station.set_station(2)   # activate the 2nd station
                print(client.station.station_id)
        """
        if 1 <= id <= self._total:
            self._station = id
            self.refresh_station()
        else:
            msg = (
                f"{self.__class__.__name__} - set_station: "
                f"Input id ({id}) not in 1 => {self._total}."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

    def refresh_station(self) -> None:
        """Reload all attributes from the cached data.

        Useful after changing the station index via :meth:`set_station`,
        or to synchronise properties following an update to :attr:`all_data`.

        Note:
            This method does not make a network call. To refresh data from
            the API, re-instantiate the class or call :meth:`_get_station_me`.
        """
        self._station_id    = self._get_data("id")
        self._name          = self._get_data("name")
        self._city_code     = self._get_data("city_code")
        self._status        = self._get_data("status")
        self._create_at     = self._get_data("create_at")
        self._tz_name       = self._get_data("tz_name")
        self._capacitor     = self._get_data("capacitor")
        self._install_power = self._get_data("install_power")
        self._address       = self._get_data("address")
        self._org_name      = self._get_data("org_name")
        self._warn_data     = self._get_data("warn_data")
        self._ak            = self._get_data("ak")

    # ------------------------------------------------------------------
    # Internal data access
    # ------------------------------------------------------------------

    def _get_data(self, name: str) -> Union[int, str, dict, None]:
        """Return a field from the active station's cached data.

        Accesses element ``self._station - 1`` in :attr:`_all_data` and
        returns the value of the ``name`` field.

        Args:
            name (str): Field name to read from the station dictionary.

        Returns:
            Union[int, str, dict, None]: Field value, or ``None`` if absent.

        Raises:
            MySolensoException: If the station index is ``0`` (no station
                selected).
        """
        if self._station == 0:
            msg = f"{self.__class__.__name__} - get_data: station index = 0."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        _idx = self._station - 1
        return self._all_data[_idx].get(name, None)

    # ------------------------------------------------------------------
    # Public properties — station list
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> list:
        """Full raw list of all stations returned by the API.

        Example:
             [
                {
                    "id": 9999999,
                    "name": "JOHN DOE",
                    "city_code": "FR13005000000000",
                    "parent_city": [
                        {
                            "id": 69,
                            "pid": 0,
                            "code": "FR00000000000000",
                            "weather_of_cid": 0,
                            "city_name": "France",
                            "country_code": "FR",
                            "level": 1
                        }
                    ],
                    "status": 40,
                    "classify": 1,
                    "create_by": 293382,
                    "create_by_name": "JDOE",
                    "create_at": "2025-11-08 10:44:51",
                    "tz_name": "UTC+01",
                    "pic_path": "",
                    "capacitor": "5",
                    "install_power": "0",
                    "address": "95 Moon Road, 99999 Galaxy, World",
                    "owner_name": "John Doe",
                    "gid": 123456,
                    "org_name": "Install Solenso",
                    "is_stars": 0,
                    "is_balance": 0,
                    "is_reflux": 0,
                    "warn_data": {
                        "s_uoff": false,
                        "s_ustable": false,
                        "s_uid": false,
                        "l3_warn": false,
                        "g_warn": false,
                        "me_warn": false,
                        "dl": null,
                        "pw_off": false
                    },
                    "nk_name": "",
                    "is_3rd": 0,
                    "dc": 0,
                    "cr": 0,
                    "ak": "aP7xQnLk9vTe41dR2mHyCuJ8zsKb"
                }
            ]
         
        Returns:
            list: List of dicts (one per station).
        """
        return self._all_data

    @property
    def station_total(self) -> int:
        """Total number of stations available for this account.

        Returns:
            int: Value of the ``total`` field returned by the API.
        """
        return self._total

    @property
    def station_ids(self) -> List[int]:
        """List of identifiers for all stations.

        Returns:
            List[int]: List of ``id`` fields from each station.
            Malformed entries are silently ignored.

        Example:
            ::

                print(client.station.station_ids)  # [42, 43]
        """
        ids = []
        for item in self._all_data:
            try:
                ids.append(item["id"])
            except (TypeError, KeyError):
                continue
        return ids

    @property
    def stations(self) -> List[dict]:
        """Summary list of all stations (id + AK key).

        Returns:
            List[dict]: List of ``{"id": ..., "ak": ...}`` dicts for each
            station. Malformed entries are silently ignored.

        Example:
            ::

                for s in client.station.stations:
                    print(s["id"], s["ak"])
        """
        stations = []
        for item in self._all_data:
            try:
                stations.append({"id": item["id"], "ak": item["ak"]})
            except (TypeError, KeyError):
                continue
        return stations

    # ------------------------------------------------------------------
    # Public properties — active station
    # ------------------------------------------------------------------

    @property
    def station_id(self) -> int:
        """Unique identifier of the active station.

        Returns:
            int: ``id`` field of the current station.
        """
        return self._station_id

    @property
    def name(self) -> str:
        """Name of the active photovoltaic installation.

        Returns:
            str: ``name`` field of the current station.
        """
        return self._name

    @property
    def city_code(self) -> str:
        """City code where the station is located.

        Returns:
            str: ``city_code`` field of the current station.
        """
        return self._city_code

    @property
    def status(self) -> int:
        """Operational status of the station.

        Returns:
            int: ``status`` field of the current station
            (``1`` = online, other values = offline or alarm).
        """
        return self._status

    @property
    def create_at(self) -> str:
        """Date the station was registered on the platform.

        Returns:
            str: ``create_at`` field (ISO 8601 format or similar).
        """
        return self._create_at

    @property
    def tz_name(self) -> str:
        """Timezone of the station (e.g. ``"UTC+01"``).

        Returns:
            str: ``tz_name`` field of the current station.
        """
        return self._tz_name

    @property
    def capacitor(self) -> str:
        """Solar panel capacity associated with the station (kVA).

        Returns:
            str: ``capacitor`` field of the current station.
        """
        return self._capacitor

    @property
    def install_power(self) -> str:
        """Installed power of the station.

        Returns:
            str: ``install_power`` field of the current station.
        """
        return self._install_power

    @property
    def address(self) -> str:
        """Full geographic address of the station.

        Returns:
            str: ``address`` field of the current station.
        """
        return self._address

    @property
    def org_name(self) -> str:
        """Name of the organisation that owns the station.

        Returns:
            str: ``org_name`` field of the current station.
        """
        return self._org_name

    @property
    def warn_data(self) -> dict:
        """Alarm/warning data for the station.

        Returns:
            dict: ``warn_data`` field of the current station.
        """
        return self._warn_data

    @property
    def ak(self) -> str:
        """Access key (API Key) specific to this station.

        Used for calls to the associated Hoymiles API.

        Returns:
            str: ``ak`` field of the current station.
        """
        return self._ak
