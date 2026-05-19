from __future__ import annotations

import logging
from typing import Any

from ...post import MySolensoPost
from ...const import API_STATION_INFO_DEVICE
from ...exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoStationInfoDevice:

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
            self._get_station_info_device()


    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_station_info_device(self) -> None:

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
            response = self._client.post(API_STATION_INFO_DEVICE)

            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_station_info_device: "
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
            self._sn          = _clean(self._all_data.get("sn"))
            self._connect     = _clean(self._all_data.get("warn_data").get("connect"))
            self._warn        = _clean(self._all_data.get("warn_data").get("warn"))
            self._vc          = _clean(self._all_data.get("vc"))
            self._dtu_sn      = _clean(self._all_data.get("dtu_sn"))
            self._type        = _clean(self._all_data.get("type"))
            self._version     = _clean(self._all_data.get("version"))
            self._replace_num = _clean(self._all_data.get("replace_num"))
            self._model_no    = _clean(self._all_data.get("model_no"))
            self._soft_ver    = _clean(self._all_data.get("soft_ver"))
            self._hard_ver    = _clean(self._all_data.get("hard_ver"))
            self._extend_data = _clean(self._all_data.get("extend_data"))
            self._children    = _clean(self._all_data.get("children"))


        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def station_info_device_refresh(self) -> None:

        self._get_station_info_device()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        """_summary_

        Returns:
            {
                "sn": "D0100289H",
                "warn_data": {
                    "_rw": "",
                    "connect": true,
                    "warn": false
                },
                "id": 1456060,
                "vc": "289",
                "dtu_sn": "D0100289H",
                "type": 1,
                "version": 3,
                "replace_num": 0,
                "model_no": "HD-Insight",
                "soft_ver": "V00.00.06",
                "hard_ver": "H12.02.02",
                "extend_data": {},
                "children": [
                    {
                        "sn": "A11001X4A",
                        "warn_data": {
                            "warn": false,
                            "connect": true
                        },
                        "id": 7454520,
                        "vc": "2L2",
                        "dtu_sn": "D0100289H",
                        "type": 3,
                        "version": 3,
                        "replace_num": 0,
                        "model_no": "Sol-H1000H",
                        "soft_ver": "V01.00.04",
                        "hard_ver": "H00.04.00",
                        "extend_data": {
                            "dmt": 0,
                            "grid_name": "",
                            "route": 0,
                            "port_array": [
                                1,
                                2
                            ],
                            "grid_id": 0,
                            "grid_version": ""
                        },
                        "children": []
                    },
                    {
                        "sn": "A110016VJ",
                        "warn_data": {
                            "warn": false,
                            "connect": true
                        },
                        "id": 6654200,
                        "vc": "22L",
                        "dtu_sn": "D0100289H",
                        "type": 3,
                        "version": 3,
                        "replace_num": 0,
                        "model_no": "Sol-H1000H",
                        "soft_ver": "V01.00.04",
                        "hard_ver": "H00.04.00",
                        "extend_data": {
                            "dmt": 0,
                            "grid_name": "",
                            "route": 0,
                            "port_array": [
                                1,
                                2
                            ],
                            "grid_id": 0,
                            "grid_version": ""
                        },
                        "children": []
                    },
                    {
                        "sn": "A110016L3",
                        "warn_data": {
                            "warn": false,
                            "connect": true
                        },
                        "id": 6654210,
                        "vc": "212",
                        "dtu_sn": "D0100289H",
                        "type": 3,
                        "version": 3,
                        "replace_num": 0,
                        "model_no": "Sol-H1000H",
                        "soft_ver": "V01.00.04",
                        "hard_ver": "H00.04.00",
                        "extend_data": {
                            "dmt": 0,
                            "grid_name": "",
                            "route": 0,
                            "port_array": [
                                1,
                                2
                            ],
                            "grid_id": 0,
                            "grid_version": ""
                        },
                        "children": []
                    },
                    {
                        "sn": "A110016GV",
                        "warn_data": {
                            "warn": false,
                            "connect": true
                        },
                        "id": 6654230,
                        "vc": "23D",
                        "dtu_sn": "D0100289H",
                        "type": 3,
                        "version": 3,
                        "replace_num": 0,
                        "model_no": "Sol-H1000H",
                        "soft_ver": "V01.00.08",
                        "hard_ver": "H00.04.00",
                        "extend_data": {
                            "dmt": 0,
                            "grid_name": "",
                            "route": 0,
                            "port_array": [
                                1,
                                2
                            ],
                            "grid_id": 0,
                            "grid_version": ""
                        },
                        "children": []
                    },
                    {
                        "sn": "A110016B1",
                        "warn_data": {
                            "warn": false,
                            "connect": true
                        },
                        "id": 6654220,
                        "vc": "2BD",
                        "dtu_sn": "D0100289H",
                        "type": 3,
                        "version": 3,
                        "replace_num": 0,
                        "model_no": "Sol-H1000H",
                        "soft_ver": "V01.00.04",
                        "hard_ver": "H00.04.00",
                        "extend_data": {
                            "dmt": 0,
                            "grid_name": "",
                            "route": 0,
                            "port_array": [
                                1,
                                2
                            ],
                            "grid_id": 0,
                            "grid_version": ""
                        },
                        "children": []
                    }
                ]
            }
        """
        return self._all_data

    @property
    def sn(self) -> str:
        return self._sn
    
    @property
    def connect(self) -> bool:
        return self._connect
    
    @property
    def warn(self) -> bool:
        return self._warn
    
    @property
    def vc(self) -> str:
        return self._vc
    
    @property
    def dtu_sn(self) -> str:
        return self._dtu_sn
    
    @property
    def type(self) -> int:
        return self._type

    @property
    def version(self) -> int:
        return self._version
    
    @property
    def replace_num(self) -> int:
        return self._replace_num

    @property
    def model_no(self) -> str:
        return self._model_no
    
    @property
    def soft_ver(self) -> str:
        return self._soft_ver
    
    @property
    def hard_ver(self) -> str:
        return self._hard_ver
    
    @property
    def list_dtu(self) -> list[dict]:
        
        data_list = self._children

        # Guard against an uninitialised or empty data store.
        if not data_list:
            raise ValueError("all_data is missing or empty")

        # Return a minimal projection: date + pv_eq only.
        return [
            {
                "sn"     : item["sn"],
                "dtu_sn" : item["dtu_sn"]
            }
            for item in data_list
        ]
    
    @property
    def list_dtu_info(self) -> list[dict]:
        
        data_list = self._children

        # Guard against an uninitialised or empty data store.
        if not data_list:
            raise ValueError("all_data is missing or empty")

        # Return a minimal projection: date + pv_eq only.
        return [
            {
                "sn"   : item["sn"],
                "dtu_sn"   : item["dtu_sn"],
                "warn": item["warn_data"].get("warn"),
                "connect": item["warn_data"].get("connect"),
                "vc"   : item["vc"],
                "type"   : item["type"],
                "version"   : item["version"],
                "replace_num"   : item["replace_num"],
                "model_no"   : item["model_no"],
                "soft_ver"   : item["soft_ver"],
                "hard_ver"   : item["hard_ver"]
            }
            for item in data_list
        ]