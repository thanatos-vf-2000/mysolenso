from __future__ import annotations

import logging
from typing import Union, List

from ..post import MySolensoPost
from ..const import API_STATION_FIND
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)

class MySolensoStationData:
    def __init__(self, parent) -> None:
        self.parent = parent
        if self.parent.station.station_id is None:
            _LOG.warning("%s - MySolensoStationData station_id is None.", self.__class__.__name__)
            raise MySolensoException("MySolensoStationData station_id is None.")
        
        self._station_find = self.parent.station.station_id
        
        # Fetch the station list (sets total and all_data)
        self._get_station_find()
    
    def set_station_find(self, id: int) -> None:
        stations = self.parent.station.stations
        exists = any(
            station.get("id") == id
            for station in stations
        )
        if exists == False:
            msg = f"{self.__class__.__name__} - set_station_find: station {id} not found."
            _LOG.warning(msg)
            raise MySolensoException(msg)
        self._station_find = id
        self._get_station_find()
        
    def _get_station_find(self) -> None:
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            
            self._client.set_raw_payload({"ERROR_BACK": True,"body":{"id":self._station_find},"WAITING_PROMISE": True})
            response = self._client.post(API_STATION_FIND)

            self._all_data = response
            
            self._name              = self._get_data("name")
            self._create_at         = self._get_data("create_at")
            self._capacitor         = self._get_data("capacitor")
            self._address           = self._get_data("address")
            self._config            = self._get_data("config")
            self._is_stars          = self._get_data("is_stars")
            self._money_unit        = self._get_data("money_unit")
            self._electricity_price = self._get_data("electricity_price")
            self._timezone          = self._get_data("timezone")
            self._local_time        = self._get_data("local_time")
            self._install_power     = self._get_data("group")
            
            

        except Exception as e:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from e
    
    def _get_data(self, name: str) -> Union[int, float, str, dict, None]:
        return self._all_data.get(name, None)
    
    @property
    def all_data(self) -> dict:
        return self._all_data
    
    @property
    def station_id(self) -> int:
        """Unique identifier of the active station.

        Returns:
            int: ``id`` field of the current station.
        """
        return self._station_find
    
    @property
    def name(self) -> str:
        """Name of the active photovoltaic installation.

        Returns:
            str: ``name`` field of the current station.
        """
        return self._name
    
    @property
    def create_at(self) -> str:
        """Date the station was registered on the platform.

        Returns:
            str: ``create_at`` field (ISO 8601 format or similar).
        """
        return self._create_at
    
    @property
    def capacitor(self) -> str:
        """Solar panel capacity associated with the station (kVA).

        Returns:
            str: ``capacitor`` field of the current station.
        """
        return self._capacitor
    
    @property
    def address(self) -> str:
        """Full geographic address of the station.

        Returns:
            str: ``address`` field of the current station.
        """
        return self._address
    
    @property
    def config(self) -> dict:
        return self._config
    
    @property
    def is_stars(self) -> int:
        return self.is_stars
    
    @property
    def money_unit(self) -> str:
        return self._money_unit
    
    @property
    def electricity_price(self) -> float:
        return self._electricity_price
    
    @property
    def timezone(self) -> dict:
        return self._timezone
    
    @property
    def local_time(self) -> str:
        return self._local_time
    
    @property
    def install_power(self) -> dict:
        return self._install_power
    
