 
from __future__ import annotations
 
import logging
from datetime import datetime, timedelta
 
from ...post import MySolensoPost
from ...const import API_OEM_COUNT
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoOEMPowerCount:
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
            self._day_min = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            self._day_min = now.strftime("%Y-%m-%d")
        
        self._day_max = self._day_min
        
    
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
            self._get_oem_power_count()
    
    def set_day(self, day_min: str, day_max: str, refresh: bool = True) -> None:
        try:
            if len(day_min) != 10:
                raise ValueError("Invalid length for day_min.")
            
            if len(day_max) != 10:
                raise ValueError("Invalid length for day_max.")

            min_date = datetime(1900, 1, 1).date()
            max_date = datetime.now().date()
            
            day_min_obj = datetime.strptime(day_min, "%Y-%m-%d").date()
            day_max_obj = datetime.strptime(day_max, "%Y-%m-%d").date()
            
            if not (min_date <= day_min_obj <= max_date):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"day_min outside the allowed range "
                    f"{min_date} <= {day_min} <= {max_date}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
            if not (min_date <= day_max_obj <= max_date):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"day_max outside the allowed range "
                    f"{min_date} <= {day_max} <= {max_date}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
            
            if not (day_min_obj <= day_max_obj):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"date day_min not less or equal to day_max."
                    f"{day_min} <= {day_max}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
 
            self._day_min = day_min
            self._day_max = day_max
            
            if refresh:
                self._get_oem_power_count()
 
        except MySolensoException:
            raise
        except ValueError:
            msg = (
                f"{self.__class__.__name__} - set_day: "
                f"'{day_min}' or {day_max} are not a valid YYYY-MM-DD date."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)
        
    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------
    def _get_oem_power_count(self) -> None:
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            self._client.set_raw_payload({
                "WAITING_PROMISE": False,
                "body":{
                    "sid_list": [self._station_id],
                    "mode": 1,
                    "start_date": self._day_min,
                    "end_date": self._day_max,
                }
            })
            response = self._client.post(API_OEM_COUNT)
 
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_oem_power_count: "
                    f"response data not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            # The API returns a list; take the first (and only) element.
            self._all_data = response
            
            def _clean(value):
                return str(value).strip() if value is not None else None

            self._total_pv = _clean(response.get("total_pv_eq"))
            self._total_consumption = _clean(response.get("total_consumption_eq"))
 
        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc
    
    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
 
    def oem_power_refresh(self) -> None:
        self._get_oem_power_count()
    
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
 
    @property
    def all_data(self) -> dict:
        """
        Data Example:
            {
                "total_pv_eq": "91.22",
                "total_consumption_eq": "0"
            }
        

        """
        return self._all_data
    
    @property
    def total_pv(self) -> str:
        return self._total_pv
    
    @property
    def total_consumption(self) -> str:
        return self._total_consumption