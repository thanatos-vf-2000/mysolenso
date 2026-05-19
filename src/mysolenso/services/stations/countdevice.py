from __future__ import annotations

import logging
from typing import Any

from ...post import MySolensoPost
from ...const import API_STATION_COUNT_DEVICE
from ...exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoStationCountDevice:

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
            self._get_station_count_device()


    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_station_count_device(self) -> None:

        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())

            # Build the request body: station list, mode, and date range.
            # Note: no pagination — this endpoint returns a single aggregate.
            self._client.set_raw_payload({
                "body":{
                    "id": self._station_id},
                "WAITING_PROMISE": True
            })
            response = self._client.post(API_STATION_COUNT_DEVICE)

            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_station_count_device: "
                    f"response data not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            # Store the complete raw response dictionary.
            self._all_data = response
            

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
            self._sn           = _clean(self._all_data.get("sn"))
            self._station_num  = _clean(self._all_data.get("station_num"))
            self._dtu_num      = _clean(self._all_data.get("dtu_num"))
            self._repeater_num = _clean(self._all_data.get("repeater_num"))
            self._mi_num       = _clean(self._all_data.get("mi_num"))
            self._au_num       = _clean(self._all_data.get("au_num"))
            self._rsd_num      = _clean(self._all_data.get("rsd_num"))
            self._op_num       = _clean(self._all_data.get("op_num"))
            self._tran_num     = _clean(self._all_data.get("tran_num"))
            self._meter_num    = _clean(self._all_data.get("meter_num"))
            self._bms_num      = _clean(self._all_data.get("bms_num"))
            self._em_num       = _clean(self._all_data.get("em_num"))


        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def station_count_device_refresh(self) -> None:

        self._get_station_count_device()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        """_summary_

        Returns:
            {
                "sn": null,
                "station_num": 1,
                "dtu_num": 1,
                "repeater_num": 0,
                "mi_num": 5,
                "inv_num": 0,
                "au_num": 0,
                "rsd_num": 0,
                "op_num": 0,
                "tran_num": 0,
                "meter_num": 0,
                "bms_num": 0,
                "em_num": 0
            }
        """
        return self._all_data

    @property
    def sn(self) -> str:
        return self._sn
    
    @property
    def station_num(self) -> int:
        return self._station_num
    
    @property
    def dtu_num(self) -> int:
        return self._dtu_num
    
    @property
    def repeater_num(self) -> int:
        return self._repeater_num
    
    @property
    def mi_num(self) -> int:
        return self._mi_num
    
    @property
    def au_num(self) -> int:
        return self._au_num
    
    @property
    def rsd_num(self) -> int:
        return self._rsd_num
    
    @property
    def op_num(self) -> int:
        return self._op_num
    
    @property
    def tran_num(self) -> int:
        return self._tran_num
    
    @property
    def meter_num(self) -> int:
        return self._meter_num
    
    @property
    def bms_num(self) -> int:
        return self._bms_num
    
    @property
    def em_num(self) -> int:
        return self._em_num
    

    