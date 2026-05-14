from __future__ import annotations

import logging
from typing import Union

from ..post import MySolensoPost
from ..const import API_STATION_COUNT
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoStationCount:
    
    def __init__(self, parent) -> None:
        self.parent = parent
        
        # Guard: station_id must be resolved before instantiation
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = self.parent.station.station_id
        
        # Initial data fetch for the active station
        self._get_station_count()
    
    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------

    def set_station_count(self, id: int) -> None:
        stations = self.parent.station.stations
        exists = any(station.get("id") == id for station in stations)

        if not exists:
            msg = (
                f"{self.__class__.__name__} - set_station_find: "
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
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            self._client.set_raw_payload({"body":{"sid":self._station_id},"WAITING_PROMISE": True})
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


        except Exception as e:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from e
    
    # ------------------------------------------------------------------
    # Internal data access
    # ------------------------------------------------------------------

    def _get_data(self, name: str) -> Union[int, str, None]:
        """Return a field from the cached station detail response.

        Args:
            name (str): Field name to read from the raw response dict.

        Returns:
            Union[int, str, None]: Field value, or ``None``
            if the key is absent.
        """
        return self._all_data.get(name, None)

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        return self._all_data

    @property
    def station_id(self) -> int:
        return self._station_id
    
    @property
    def today_eq(self) -> str:
        return self._today_eq
    
    @property
    def month_eq(self) -> str:
        return self._month_eq
    
    @property
    def year_eq(self) -> str:
        return self._year_eq
    
    @property
    def total_eq(self) -> str:
        return self._total_eq
    
    @property
    def real_power(self) -> str:
        return self._real_power
    
    @property
    def co2_emission_reduction(self) -> str:
        return self._co2_emission_reduction
    
    @property
    def plant_tree(self) -> str:
        return self._plant_tree
    
    @property
    def data_time(self) -> str:
        return self._data_time
    
    @property
    def last_data_time(self) -> str:
        return self._last_data_time
    
    @property
    def capacitor(self) -> str:
        """Solar panel capacity of the station (kVA).

        Returns:
            str: ``capacitor`` field of the station detail record.
        """
        return self._capacitor
