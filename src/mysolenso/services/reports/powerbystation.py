"""MySolenso per-station daily power aggregation service.
 
Provides the :class:`MySolensoPowerByStation` class, which queries the
``/report_select_power_by_station`` Solenso endpoint and exposes the aggregated power
data for a single station over a given date range.
 
Unlike :mod:`~mysolenso.services.powerbyday`, which uses the Hoymiles API
and returns an intra-day power curve (``HH:MM`` samples), this service
uses the Solenso API and returns a single aggregated record per station
per day - useful for day-level energy dashboards.
 
By default the service loads data for **today** (or yesterday if the local
hour is before 01:00, to avoid an empty dataset at midnight). Use
:meth:`~MySolensoPowerByStation.set_day` to query any historical date.
 
This module is intended to be instantiated by :class:`~mysolenso.MySolenso`
and accessed via ``client.powerbaystation``.
 
Example:
    ::
 
        client = MySolenso(username="user", token="tok")
 
        data = client.powerbaystation.all_data
        print(data)
 
        # Query a specific date
        client.powerbaystation.set_day("2026-01-01")
        data = client.powerbaystation.all_data
 
        # Refresh without changing station or date
        client.powerbaystation.get_power_station_refresh()
"""
 
from __future__ import annotations
 
import logging
from datetime import datetime, timedelta
 
from ...post import MySolensoPost
from ...const import API_POWER_BY_STATION
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoPowerByStation:
    """Daily aggregated power record for a single PV station.
 
    Queries the ``/report_select_power_by_station`` Solenso endpoint with a station ID
    and a date range (start = end = target date) and caches the first
    element of the response list as :attr:`all_data`.
 
    Args:
        parent: Instance of :class:`~mysolenso.MySolenso` providing access
            to the ``auth`` and ``station`` sub-modules.
 
    Raises:
        MySolensoException: If ``parent.station.station_id`` is ``None``
            (no active station resolved), or if the API call fails during
            instantiation.
 
    Attributes:
        parent: Reference to the parent :class:`~mysolenso.MySolenso` object.
 
    Note:
        Unlike :class:`~mysolenso.services.powerbyday.MySolensoPowerByDay`,
        this class does **not** automatically fetch data at construction -
        call :meth:`get_power_station_refresh` or :meth:`set_day` to trigger
        the first request.
 
    Example:
        ::
 
            client = MySolenso(username="admin", token="tok")
            pb = client.powerbaystation
 
            pb.get_power_station_refresh()
            print(pb.all_data)
 
            pb.set_day("2026-05-22")
            print(pb.all_data)
    """
 
    def __init__(self, parent) -> None:
        self.parent = parent
 
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)
 
        self._station_id = self.parent.station.station_id
 
        # Default to today; fall back to yesterday before 01:00 to avoid
        # returning an empty dataset at midnight before the first inverter
        # measurement of the day arrives.
        now = datetime.now()
        if now.hour < 1:
            self._day = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            self._day = now.strftime("%Y-%m-%d")
        #self._all_data = {}
 
    # ------------------------------------------------------------------
    # Station and date selection
    # ------------------------------------------------------------------
 
    def set_station(self, id: int, refresh: bool = True) -> None:
        """Switch the active station and optionally reload power data.
 
        The provided ``id`` is validated against the station list from
        :attr:`~mysolenso.services.station.MySolensoStation.stations`.
 
        Args:
            id (int): Station ID to activate. Must exist in the account's
                station list.
            refresh (bool): If ``True`` (default), immediately calls
                :meth:`_get_power_by_station` to reload data for the new
                station. Set to ``False`` to defer the network call.
 
        Raises:
            MySolensoException: If ``id`` is not found in the account's
                station list, or if the subsequent API call fails.
 
        Example:
            ::
 
                client.powerbaystation.set_station(43)
                print(client.powerbaystation.all_data)
        """
        stations = self.parent.station.stations
        if not any(station.get("id") == id for station in stations):
            msg = (
                f"{self.__class__.__name__} - set_station: "
                f"station {id} not found."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)
 
        self._station_id = id
        if refresh:
            self._get_power_by_station()
 
    def set_day(self, day: str, refresh: bool = True) -> None:
        """Set the queried date and optionally reload power data.
 
        Args:
            day (str): Date string in ``YYYY-MM-DD`` format. Must be between
                ``1900-01-01`` and today (inclusive).
            refresh (bool): If ``True`` (default), immediately reloads data
                for the new date. Set to ``False`` to defer the call.
 
        Raises:
            MySolensoException: If ``day`` is not in ``YYYY-MM-DD`` format,
                is outside the allowed range, or if the API call fails.
 
        Example:
            ::
 
                client.powerbaystation.set_day("2026-05-22")
                print(client.powerbaystation.all_data)
        """
        try:
            if len(day) != 10:
                raise ValueError("Invalid length.")
 
            date_obj = datetime.strptime(day, "%Y-%m-%d").date()
 
            min_date = datetime(1900, 1, 1).date()
            max_date = datetime.now().date()
 
            if not (min_date <= date_obj <= max_date):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"date outside the allowed range "
                    f"{min_date} <= {date_obj} <= {max_date}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
 
            self._day = day
            if refresh:
                self._get_power_by_station()
 
        except MySolensoException:
            raise
        except ValueError:
            msg = (
                f"{self.__class__.__name__} - set_day: "
                f"'{day}' is not a valid YYYY-MM-DD date."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)
 
    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------
 
    def _get_power_by_station(self) -> None:
        """Query the API and cache the aggregated station power record.
 
        Sends a POST to :data:`~mysolenso.const.API_POWER_BY_STATION` with
        a payload containing the station ID and the queried date as both
        ``start_date`` and ``end_date`` (single-day window).
 
        The response is expected to be a non-empty list; the first element
        is stored in :attr:`all_data`.
 
        Raises:
            MySolensoException: If the response list is empty, if a network
                or HTTP error occurs, or if the JSON is malformed.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            self._client.set_raw_payload({
                "WAITING_PROMISE": False,
                "body": {
                    "sid_list":   [self._station_id],
                    "start_date": self._day,
                    "end_date":   self._day,
                },
            })
            response = self._client.post(API_POWER_BY_STATION)
 
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_power_by_station: "
                    f"response data not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
 
            # The API returns a list; take the first (and only) element.
            self._all_data = response[0]
 
        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc
 
    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
 
    def get_power_station_refresh(self) -> None:
        """Re-fetch power data for the current station and date.
 
        Triggers a new call to :meth:`_get_power_by_station` without
        changing the active station ID or the queried date. Useful for
        polling the latest values during the day.
 
        Example:
            ::
 
                # Poll every 5 minutes
                import time
                while True:
                    client.powerbaystation.get_power_station_refresh()
                    print(client.powerbaystation.all_data)
                    time.sleep(300)
        """
        self._get_power_by_station()
 
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
 
    @property
    def all_data(self) -> dict:
        """Full raw record returned by the ``/report_select_power_by_station`` endpoint.
 
        Contains the aggregated power fields for the active station on the
        queried date (fields depend on the API version; typically include
        production totals, peak power, and timestamps).

        Data Example:
            {
            "sid": 9876543,
            "name": "DOE JOHN",
            "tz_name": "UTC+01",
            "is_reflux": 0,
            "is_balance": 0,
            "meter_location": 0,
            "classify": 1,
            "dw": null,
            "data_list": [
                {
                    "date": "06:15",
                    "pv_power": "26",
                    "consumption_power": "0",
                    "meter_c_power": "0",
                    "grid_p_power": "0",
                    "bms_power": "0",
                    "meter_location": 0
                },
                ...
                {
                    "date": "22:00",
                    "pv_power": "0",
                    "consumption_power": "0",
                    "meter_c_power": "0",
                    "grid_p_power": "0",
                    "bms_power": "0",
                    "meter_location": 0
                },
                {
                    "date": "22:15",
                    "pv_power": "0",
                    "consumption_power": "0",
                    "meter_c_power": "0",
                    "grid_p_power": "0",
                    "bms_power": "0",
                    "meter_location": 0
                }
            ]
        }
        
        Returns:
            dict: First element of the API response list for the active
            station and date.
 
        Raises:
            AttributeError: If :meth:`get_power_station_refresh` or
                :meth:`set_day` has not been called yet (``_all_data`` not
                initialised).
 
        Example:
            ::
 
                client.powerbaystation.get_power_station_refresh()
                data = client.powerbaystation.all_data
                print(data)
        """
        return self._all_data
    
    @property
    def extract_power_data(self) -> list[dict]:
        """
        Extracts only:
        - date
        - power (from pv_power)

        Expected output example:
        [
            {"date": "06:15", "power": 26},
            {"date": "06:30", "power": 56},
        ]

        Returns:
            list[dict]: A simplified list containing only date and power values.

        Raises:
            ValueError: If `data_list` is missing or empty.
        """

        data_list = self._all_data.get("data_list")

        if not data_list:
            raise ValueError("data_list is missing or empty")

        return [
            {
                "date": item["date"],
                "power": int(item["pv_power"])
            }
            for item in data_list
        ]