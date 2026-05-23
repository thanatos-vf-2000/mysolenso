from __future__ import annotations
 
import logging
from typing import Any
 
from ...post import MySolensoPost
from ...const import API_STATION_ARRAY
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoStationArray:
 
    def __init__(self, parent) -> None:
        self.parent = parent
 
        # Validate that a station has already been selected by the parent.
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)
 
        self._station_id = self.parent.station.station_id
 
 
    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------
 
    def set_station(self, id: int, refresh: bool = True) -> None:
        """Switch the active station for device count queries.
 
        Args:
            id (int): ID of the target station. Must exist in the account's
                station list.
            refresh (bool): When ``True`` (default), immediately re-fetches
                the device counts for the new station.
 
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
            self._get_station_array()
 
 
    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------
 
    def _get_station_array(self) -> None:
 
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
 
            # Build the request body: station list, mode, and date range.
            # Note: no pagination - this endpoint returns a single aggregate.
            self._client.set_raw_payload({
                "body":{
                    "id": self._station_id},
                "WAITING_PROMISE": True
            })
            response = self._client.post(API_STATION_ARRAY)
 
            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_station_array: "
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
            self._id          = _clean(self._all_data.get("id"))
            self._name        = _clean(self._all_data.get("name"))
            self._angle_tilt  = _clean(self._all_data.get("angle_tilt"))
            self._orientation = _clean(self._all_data.get("orientation"))
            self._row         = _clean(self._all_data.get("row"))
            self._column      = _clean(self._all_data.get("column"))
            self._pattern     = _clean(self._all_data.get("pattern"))
            self._layout_tilt = _clean(self._all_data.get("layout_tilt"))
            self._e_min_x     = _clean(self._all_data.get("e_min_x"))
            self._e_min_y     = _clean(self._all_data.get("e_min_y"))
 
        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc
 
    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
 
    def station_array_refresh(self) -> None:
        """Force a fresh fetch of device layout data from the API."""
        self._get_station_array()
 
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
 
    @property
    def all_data(self) -> dict:
        """
 
        Returns:
            dict: Device count summary. Example::

            {
                "id": 268104,
                "name": "DOE JOHN,
                "angle_tilt": 20,
                "orientation": 0,
                "row": 0,
                "column": 9,
                "pattern": 1,
                "layout_tilt": 0,
                "e_min_x": 0,
                "e_min_y": 0
            }
                
        """
        return self._all_data
 
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def angle_tilt(self) -> int:
        return self._angle_tilt
    
    @property
    def orientation(self) -> int:
        return self._orientation
    
    @property
    def row(self) -> int:
        return self._row
    
    @property
    def column(self) -> int:
        return self._column
    
    @property
    def pattern(self) -> int:
        return self.pattern
    
    @property
    def layout_tilt(self) -> int:
        return self._layout_tilt
    
    @property
    def e_min_x(self) -> int:
        return self._e_min_x
    
    @property
    def e_min_y(self) -> int:
        return self._e_min_y
