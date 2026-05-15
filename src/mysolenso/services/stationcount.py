"""MySolenso station energy counters service.

Provides the :class:`MySolensoStationCount` class, which queries the
``/data_count_station_real_data`` endpoint and exposes the cumulative and
real-time energy production counters for a single PV station.

Returned metrics include today's yield, monthly and yearly totals, lifetime
production, current real power, CO₂ savings, equivalent trees planted, and
timestamps for the latest data update.

This module is instantiated automatically by :class:`~mysolenso.MySolenso`
and accessible via ``client.stationcount``.

Example:
    ::

        client = MySolenso(username="user", token="tok")

        print(client.stationcount.today_eq)    # e.g. "12.34"  (kWh today)
        print(client.stationcount.total_eq)    # e.g. "4521.0" (kWh lifetime)
        print(client.stationcount.real_power)  # e.g. "2048"   (W, current)
        print(client.stationcount.co2_emission_reduction)
        print(client.stationcount.last_data_time)
"""

from __future__ import annotations

import logging
from typing import Union

from ..post import MySolensoPost
from ..const import API_STATION_COUNT
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoStationCount:
    """Real-time and cumulative energy counters for a single PV station.

    Queries the ``/data_count_station_real_data`` Solenso endpoint and
    caches the response. All production metrics are exposed as read-only
    properties.

    Args:
        parent: Instance of :class:`~mysolenso.MySolenso` providing access
            to the ``auth`` and ``station`` sub-modules.

    Raises:
        MySolensoException: If ``parent.station.station_id`` is ``None``,
            or if the API response is invalid.

    Attributes:
        parent: Reference to the parent :class:`~mysolenso.MySolenso` object.

    Example:
        ::

            client = MySolenso(username="jdoe", token="tok")
            sc = client.stationcount

            print(sc.today_eq)               # today's yield in kWh
            print(sc.month_eq)               # month-to-date yield in kWh
            print(sc.year_eq)                # year-to-date yield in kWh
            print(sc.total_eq)               # lifetime yield in kWh
            print(sc.real_power)             # current AC output in W
            print(sc.co2_emission_reduction) # CO₂ saved in kg
            print(sc.plant_tree)             # equivalent trees planted
            print(sc.data_time)              # data timestamp
            print(sc.last_data_time)         # last measurement timestamp
            print(sc.capacitor)              # installed capacity in kWp
    """

    def __init__(self, parent) -> None:
        self.parent = parent

        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = self.parent.station.station_id
        self._get_station_count()

    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------

    def set_station_count(self, id: int) -> None:
        """Switch the active station and reload all counters from the API.

        Args:
            id (int): Station ID to activate. Must exist in the account's
                station list.

        Raises:
            MySolensoException: If ``id`` is not found in the account's
                station list, or if the API call fails.

        Example:
            ::

                client.stationcount.set_station_count(43)
                print(client.stationcount.today_eq)
        """
        stations = self.parent.station.stations
        if not any(station.get("id") == id for station in stations):
            msg = (
                f"{self.__class__.__name__} - set_station_count: "
                f"station {id} not found."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = id
        self._get_station_count()

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_station_count(self) -> None:
        """Query the API and cache the station energy counters.

        Sends a POST request to :data:`~mysolenso.const.API_STATION_COUNT`
        with the current station ID wrapped in the Solenso RAW payload
        format, then maps each response field onto a private attribute.

        Raises:
            MySolensoException: If the request fails, times out, or the
                JSON response is malformed.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            self._client.set_raw_payload({
                "body": {"sid": self._station_id},
                "WAITING_PROMISE": True,
            })
            response = self._client.post(API_STATION_COUNT)

            self._all_data = response

            self._today_eq               = self._get_data("today_eq")
            self._month_eq               = self._get_data("month_eq")
            self._year_eq                = self._get_data("year_eq")
            self._total_eq               = self._get_data("total_eq")
            self._real_power             = self._get_data("real_power")
            self._co2_emission_reduction = self._get_data("co2_emission_reduction")
            self._plant_tree             = self._get_data("plant_tree")
            self._data_time              = self._get_data("data_time")
            self._last_data_time         = self._get_data("last_data_time")
            self._capacitor              = self._get_data("capacitor")

        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

    # ------------------------------------------------------------------
    # Internal data access
    # ------------------------------------------------------------------

    def _get_data(self, name: str) -> Union[int, float, str, None]:
        """Return a field from the cached station counter response.

        Args:
            name (str): Field name to read from the raw response dict.

        Returns:
            Union[int, float, str, None]: Field value, or ``None`` if the
            key is absent.
        """
        return self._all_data.get(name, None)

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        """Full raw response returned by the ``/data_count_station_real_data`` endpoint.

        Useful for accessing fields not exposed by the other properties.

        Example:
            {
                "is_null": 0,
                "today_eq": "17647.0",
                "month_eq": "241047",
                "year_eq": "1769064",
                "total_eq": "14685977",
                "real_power": "0",
                "co2_emission_reduction": "14641919.069",
                "plant_tree": "800",
                "data_time": "2026-05-14 21:20:06",
                "last_data_time": "2026-05-14 21:20:06",
                "capacitor": "5",
                "is_balance": 0,
                "is_reflux": 0,
                "pv2": 0,
                "clp": 200
            }
            
        Returns:
            dict: Complete ``data`` dictionary from the API response.
        """
        return self._all_data

    @property
    def station_id(self) -> int:
        """Identifier of the station currently loaded.

        Returns:
            int: Station ID used for the last API call.
        """
        return self._station_id

    @property
    def today_eq(self) -> str:
        """Energy produced today (Wh).

        Returns:
            str: ``today_eq`` field from the API response.
        """
        return self._today_eq

    @property
    def month_eq(self) -> str:
        """Energy produced in the current calendar month (Wh).

        Returns:
            str: ``month_eq`` field from the API response.
        """
        return self._month_eq

    @property
    def year_eq(self) -> str:
        """Energy produced in the current calendar year (Wh).

        Returns:
            str: ``year_eq`` field from the API response.
        """
        return self._year_eq

    @property
    def total_eq(self) -> str:
        """Lifetime energy produced by the station (Wh).

        Returns:
            str: ``total_eq`` field from the API response.
        """
        return self._total_eq

    @property
    def real_power(self) -> str:
        """Current AC output power of the station (W).

        This value reflects the instantaneous grid injection measured at
        the time of the last data update.

        Returns:
            str: ``real_power`` field from the API response.
        """
        return self._real_power

    @property
    def co2_emission_reduction(self) -> str:
        """Cumulative CO₂ emissions avoided by the station (kg).

        Calculated from lifetime production using a platform-defined
        carbon intensity factor.

        Returns:
            str: ``co2_emission_reduction`` field from the API response.
        """
        return self._co2_emission_reduction

    @property
    def plant_tree(self) -> str:
        """Equivalent number of trees planted, based on CO₂ savings.

        A symbolic metric provided by the Solenso platform.

        Returns:
            str: ``plant_tree`` field from the API response.
        """
        return self._plant_tree

    @property
    def data_time(self) -> str:
        """Timestamp of the data record returned by the API.

        Returns:
            str: ``data_time`` field (format depends on API; typically
            ``YYYY-MM-DD HH:MM:SS`` or Unix epoch).
        """
        return self._data_time

    @property
    def last_data_time(self) -> str:
        """Timestamp of the most recent inverter measurement received.

        Returns:
            str: ``last_data_time`` field from the API response.
        """
        return self._last_data_time

    @property
    def capacitor(self) -> str:
        """Installed peak power of the station (kWp).

        Returns:
            str: ``capacitor`` field from the API response.
        """
        return self._capacitor
