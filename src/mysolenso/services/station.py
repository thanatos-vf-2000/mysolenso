from __future__ import annotations
import logging
from typing import Union

from ..post import MySolensoPost

from ..const import API_STATION_ME
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)

class MySolensoStation:
    
    def __init__(self, parent):
        self.parent = parent
        self._get_station_me()
        
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
        self.refresh_station()

        
    def _get_station_me(self):
        try:
                
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            response = self._client.post(API_STATION_ME)
            
            self._total      = int(response.get("total", 0))
            self._all_data   = response.get("list", {})
            self._station = 1
            
        except Exception as e:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from e
        
        if self._total == 0:
            self._station = 0
            _LOG.warning("%s - MySolensoStation no data.", self.__class__.__name__)
            raise MySolensoException("MySolensoStation no data.")
    
    @property
    def all_data(self) -> dict:
        return self._all_data
    
    def set_station(
        self,
        id: int,
    ) -> None:
        if id <= self._total and id < 0:
            self._station = id
            self.refresh_station()
        else:
            _LOG.warning("%s - set_station: Input id (%i) not in 0 => %i.", (self.__class__.__name__, id, self._total))
            raise MySolensoException(f"{self.__class__.__name__} - set_station: Input id ({id}) not in 0 => {self._total}.")
        
        
    def _get_data(
        self,
        name: str,
    ) -> Union[int, str, dict]:
        
        if  self._station_id == 0:
            _LOG.warning("%s - get_data: station id = 0.", (self.__class__.__name__))
            raise MySolensoException(f"{self.__class__.__name__} - get_data: station id = 0.")
        
        _station = self._station - 1
        return self._all_data[_station].get(name, None)
    
    def refresh_station(self):
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
        
    @property
    def station_total(self) -> int:
        return self._total
    
    @property
    def station_ids(self) -> dict:
        ids = []

        for item in self._all_data:
            try:
                ids.append(item["id"])
            except (TypeError, KeyError):
                continue

        return ids

    @property
    def stations(self) -> list[dict]:
        stations = []

        for item in self._all_data:
            try:
                stations.append({
                    "id": item["id"],
                    "ak": item["ak"]
                })
            except (TypeError, KeyError):
                continue

        return stations
    
    @property
    def station_id(self) -> int:
        return self._station_id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def city_code(self) -> str:
        return self._city_code
    
    @property
    def status(self) -> int:
        return self._status
    
    @property
    def create_at(self) -> str:
        return self._create_at
    
    @property
    def tz_name(self) -> str:
        return self._tz_name
    
    @property
    def capacitor(self) -> str:
        return self._capacitor
    
    @property
    def install_power(self) -> str:
        return self._install_power
    
    @property
    def address(self) -> str:
        return self._address
    
    @property
    def org_name(self) -> str:
        return self._org_name
    
    @property
    def warn_data(self) -> dict:
        return self._warn_data

    @property
    def ak(self) -> str:
        return self._ak
