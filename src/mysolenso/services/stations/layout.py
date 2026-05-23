from __future__ import annotations
 
import logging
from typing import Any
 
from ...post import MySolensoPost
from ...const import API_STATION_LAYOUT
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoStationLayout:
 
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
            self._get_station_layout()
 
 
    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------
 
    def _get_station_layout(self) -> None:
 
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
            response = self._client.post(API_STATION_LAYOUT)
 
            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_station_layout: "
                    f"response data not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
 
            # Store the complete raw response dictionary.
            self._all_data = response
            
 
        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc
 
    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
 
    def station_layout_refresh(self) -> None:
        """Force a fresh fetch of device layout data from the API."""
        self._get_station_layout()
 
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
 
    @property
    def all_data(self) -> dict:
        """
 
        Returns:
            dict: Device count summary. Example::

                [{
                    "id": 8967081,
                    "aid": 268104,
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "dev_type": 3,
                    "mi_id": 6654200,
                    "mi_sn": "A110016VJ",
                    "port": 1,
                    "x": 0,
                    "y": 8
                },
                {
                    "id": 8967082,
                    "aid": 268104,
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "dev_type": 3,
                    "mi_id": 6654200,
                    "mi_sn": "A110016VJ",
                    "port": 2,
                    "x": 0,
                    "y": 9
                },
                {
                    "id": 8967077,
                    "aid": 268104,
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "dev_type": 3,
                    "mi_id": 6654210,
                    "mi_sn": "A110016L3",
                    "port": 1,
                    "x": 0,
                    "y": 4
                },
                {
                    "id": 8967078,
                    "aid": 268104,
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "dev_type": 3,
                    "mi_id": 6654210,
                    "mi_sn": "A110016L3",
                    "port": 2,
                    "x": 0,
                    "y": 5
                },
                {
                    "id": 8967073,
                    "aid": 268104,
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "dev_type": 3,
                    "mi_id": 6654220,
                    "mi_sn": "A110016B1",
                    "port": 1,
                    "x": 0,
                    "y": 0
                },
                {
                    "id": 8967074,
                    "aid": 268104,
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "dev_type": 3,
                    "mi_id": 6654220,
                    "mi_sn": "A110016B1",
                    "port": 2,
                    "x": 0,
                    "y": 1
                },
                {
                    "id": 8967075,
                    "aid": 268104,
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "dev_type": 3,
                    "mi_id": 6654230,
                    "mi_sn": "A110016GV",
                    "port": 1,
                    "x": 0,
                    "y": 2
                },
                {
                    "id": 8967076,
                    "aid": 268104,
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "dev_type": 3,
                    "mi_id": 6654230,
                    "mi_sn": "A110016GV",
                    "port": 2,
                    "x": 0,
                    "y": 3
                }]
        """
        return self._all_data
 
    @property
    def list_dtu(self) -> list[dict]:
        
        data_list = self._all_data
 
        # Guard against an uninitialised or empty data store.
        if not data_list:
            raise ValueError("all_data is missing or empty")
 
        seen_dtu_ids = set()
        result = []

        for item in data_list:
            dtu_id = item["dtu_id"]

            # Ignore les doublons
            if dtu_id in seen_dtu_ids:
                continue

            seen_dtu_ids.add(dtu_id)

            result.append({
                "dtu_id": item["dtu_id"],
                "dtu_sn": item["dtu_sn"]
            })

        return result
    
    def list_dtu_ids(self) -> list[int]:

        if not self._all_data:
            raise ValueError("all_data is missing or empty")

        return list({item["dtu_id"] for item in self._all_data})
    
    @property
    def list_micro_all(self) -> list[dict]:
        
        data_list = self._all_data
 
        # Guard against an uninitialised or empty data store.
        if not data_list:
            raise ValueError("all_data is missing or empty")
 
        seen_micro_ids = set()
        result = []

        for item in data_list:
            micro_id = item["dtu_id"]

            # Ignore les doublons
            if micro_id in seen_micro_ids:
                continue

            seen_micro_ids.add(micro_id)

            result.append({
                "id": item["mi_id"],
                "sn": item["mi_sn"],
                "port_dtu": item["port"]
            })

        return result
    
    def get_mi_info_by_dtu(self, dtu_id: int) -> list[dict]:

        data_list = self._all_data

        if not data_list:
            raise ValueError("all_data is missing or empty")

        result = []

        for item in data_list:
            if item.get("dtu_id") == dtu_id:
                result.append({
                    "id": item.get("mi_id"),
                    "sn": item.get("mi_sn"),
                    "port": item.get("port"),
                    "x": item.get("x"),
                    "y": item.get("y"),
                })

        return sorted(result, key=lambda d: (d["x"], d["y"]))