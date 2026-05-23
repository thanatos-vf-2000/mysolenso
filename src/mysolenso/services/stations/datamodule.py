"""Daily module data download descriptor service for MySolenso.

This module provides :class:`MySolensoStationDataModuleDay`, which retrieves the
download descriptor (URL and HTTP method) for the raw daily module data file of
the active station.  The actual binary data must be fetched separately using the
URL exposed by :attr:`~MySolensoStationDataModuleDay.full_url`.
"""
 
from __future__ import annotations
 
import logging
from typing import Any
from datetime import datetime, timedelta
 
from ...post import MySolensoPost
from ...const import API_STATION_DATA_MODULE_DAY, BASE_URL_SOLENSO
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoStationDataModuleDay:
    """Retrieve the daily module data download descriptor for the active station.

    Wraps the :data:`~mysolenso.const.API_STATION_DATA_MODULE_DAY` endpoint and
    exposes the station id, date, and download URL via typed properties.
    Call :meth:`station_data_module_day_refresh` before accessing any property
    for the first time.

    Args:
        parent: The :class:`~mysolenso.mysolenso.MySolenso` facade instance that
            holds the active session (``parent.auth``) and station context
            (``parent.station``).

    Raises:
        MySolensoException: If no station has been selected on the parent.
    """
 
    def __init__(self, parent) -> None:
        """Initialise the data-module service and set the default query date.

        Args:
            parent: The :class:`~mysolenso.mysolenso.MySolenso` facade instance.

        Raises:
            MySolensoException: If ``parent.station.station_id`` is ``None``.
        """
        self.parent = parent
 
        # Validate that a station has already been selected by the parent.
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)
 
        self._station_id = self.parent.station.station_id
        
        # Default to today; use yesterday before 01:00 to avoid empty data
        now = datetime.now()
        if now.hour < 1:
            self._day = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            self._day = now.strftime("%Y-%m-%d")
 
 
    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------
 
    def set_station(self, id: int, refresh: bool = True) -> None:
        """Switch the active station for device tree queries.
 
        Args:
            id (int): ID of the target station. Must exist in the account's
                station list.
            refresh (bool): When ``True`` (default), immediately re-fetches
                the device tree for the new station.
 
        Raises:
            MySolensoException: If the requested station ID is not found.
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

        # Reload data for the new station unless the caller deferred it.
        if refresh:
            self._get_station_data_module_day()
            
    def set_day(self, day: str, refresh: bool = True) -> None:
        """Set the queried date and optionally reload the module descriptor.

        Args:
            day (str): Date string in ``YYYY-MM-DD`` format. Must be between
                ``1900-01-01`` and today (inclusive).
            refresh (bool): If ``True`` (default), immediately reloads the
                descriptor for the new date.

        Raises:
            MySolensoException: If ``day`` is not a valid ``YYYY-MM-DD`` date,
                is outside the allowed range, or if the API call fails.
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
                self._get_station_data_module_day()

        except MySolensoException:
            raise
        except ValueError:
            msg = (
                f"{self.__class__.__name__} - set_day: "
                f"'{day}' is not a valid YYYY-MM-DD date."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)
        
    def _get_station_data_module_day(self) -> None:
        """Fetch the module data descriptor from the API and cache the result.

        Sends a POST request to :data:`~mysolenso.const.API_STATION_DATA_MODULE_DAY`
        and stores the first element of the response in ``self._all_data``.
        Individual fields (``sid``, ``date``, ``url``, ``method``) are extracted
        and stored in private attributes.

        Raises:
            MySolensoException: On an empty/null response or any network/parse error.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
 
            # Build the request body: station list, mode, and date range.
            # Note: no pagination - this endpoint returns a single aggregate.
            self._client.set_raw_payload({
                "body":{"sid": self._station_id,
                        "date": self._day,
                        "day_num":1},
                "WAITING_PROMISE": True})
            response = self._client.post(API_STATION_DATA_MODULE_DAY)
 
            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_station_data_module_day: "
                    f"response data not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
 
            # Store the complete raw response dictionary.
            self._all_data = response[0]
            
 
            # Helper to convert None → None, everything else → stripped string.
            def _clean(
                value: str | int | float | bool | list | dict | None
            ) -> str | int | float | bool | list | dict | None:
 
                if value is None:
                    return None
 
                if isinstance(value, str):
                    return value.strip()
 
                if isinstance(value, list):
                    return [_clean(item) for item in value]
 
                if isinstance(value, dict):
                    return {
                        _clean(key): _clean(val)
                        for key, val in value.items()
                    }
 
                return value
 
            # Extract and clean the two aggregate fields.
            self._sid    = _clean(self._all_data.get("sid"))
            self._date   = _clean(self._all_data.get("date"))
            self._url    = _clean(self._all_data.get("url"))
            self._method = _clean(self._all_data.get("method"))
 
 
        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc
 
    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
 
    def station_data_module_day_refresh(self) -> None:
        """Force a fresh fetch of the device tree from the API."""
        self._get_station_data_module_day()
 
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
 
    @property
    def all_data(self) -> dict:
        """Raw API response dict for the module data descriptor.

        Returns:
            dict: Example::

                {
                    "sid": 1553580,
                    "date": "2026-05-12",
                    "url": "/api/0/module/data/down_module_day_data",
                    "method": "POST"
                }
        """
        return self._all_data
 
    @property
    def sid(self) -> int:
        """Station id associated with the descriptor."""
        return self._sid
    
    @property
    def date(self) -> str:
        """Queried date in ``YYYY-MM-DD`` format as returned by the API."""
        return self._date
    
    @property
    def url(self) -> str:
        """Relative download URL for the daily module data binary file."""
        return self._url
    
    @property
    def full_url(self) -> str:
        """Absolute download URL constructed from the Solenso base URL and :attr:`url`."""
        return BASE_URL_SOLENSO + self._url
