"""Service for retrieving detailed information about a single DTU.
 
This module provides :class:`MySolensoDTUFind`, which wraps the
``dtu_find`` Solenso endpoint. A valid DTU ID must be set via
:meth:`~MySolensoDTUFind.set_dtu` before the data is fetched.
"""
 
from __future__ import annotations
 
import logging
from typing import Any
 
from ...post import MySolensoPost
from ...const import API_DTU_FIND
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoDTUFind:
    """Retrieve the full detail record for a single DTU.
 
    Call :meth:`set_dtu` with a valid DTU ID to trigger the API request and
    populate the cached data.  The ID is validated against the DTU returned by
    :class:`~mysolenso.services.dtu.selectall.MySolensoDTUSelectAll`.
 
    Args:
        parent (MySolenso): The parent client object that holds the
            authentication context and the active station reference.
 
    Raises:
        MySolensoException: If no active station is set on the parent at
            construction time.
    """
 
    def __init__(self, parent) -> None:
        self.parent = parent
 
        # Validate that a station has already been selected by the parent.
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)
 
        self._station_id = self.parent.station.station_id
        self._dtu_id = None
 
 
    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------
 
    def set_station(self, id: int) -> None:
        """Switch the active station context (does not refresh data).
 
        Args:
            id (int): ID of the target station. Must exist in the account's
                station list.
 
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
 
    # ------------------------------------------------------------------
    # DTU selection
    # ------------------------------------------------------------------
 
    def set_dtu(self, id: int, refresh: bool = True) -> None:
        """Select the DTU to query and optionally fetch its data.
 
        The DTU ID is validated against the record returned by
        :meth:`~mysolenso.services.dtu.selectall.MySolensoDTUSelectAll.dtu_select_all_refresh`.
 
        Args:
            id (int): Internal numeric ID of the DTU to query.
            refresh (bool): When ``True`` (default), immediately fetches the
                DTU detail record from the API.
 
        Raises:
            MySolensoException: If the requested DTU ID is not found.
        """
        
        self.parent.dtuselectall.dtu_select_all_refresh()
        
        _dtu = self.parent.dtuselectall.dtu_id
 
        # Verify the requested DTU ID exists in the account.
        if _dtu != id:
            msg = (
                f"{self.__class__.__name__} - set_dtu: "
                f"DTU {id} not found ({_dtu})."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)
 
        self._dtu_id = id
 
        # Reload data for the new DTU unless the caller deferred it.
        if refresh:
            self._get_dtu_find()
            
            
    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------
 
    def _get_dtu_find(self) -> None:
 
        try:
            
            if self._dtu_id is None:
                msg = (
                    f"{self.__class__.__name__} - _get_dtu_find: "
                    f"micro id not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
 
            # Build the request body: station list, mode, and date range.
            # Note: no pagination — this endpoint returns a single aggregate.
            self._client.set_raw_payload({
                "body":{
                    "id": self._dtu_id},
                "WAITING_PROMISE": True
            })
            response = self._client.post(API_DTU_FIND)
 
            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_dtu_find: "
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
 
    def dtu_find_refresh(self) -> None:
        """Force a fresh fetch of the DTU detail record from the API."""
        self._get_dtu_find()
 
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
 
    @property
    def all_data(self) -> dict:
        """Raw API response for the DTU find endpoint.
 
        Returns:
            dict: Full DTU record including firmware versions, hardware model,
            rule configuration, and supported microinverter types. Example::
 
                {
                    "id": 1456060,
                    "sid": 1553580,
                    "classify": 1,
                    "station_name": "DOE JOHN",
                    "gw_sn": "D0100289H",
                    "sn": "D0100289H",
                    "dev_type": 1,
                    "replace_num": 0,
                    "create_by": 293382,
                    "create_at": "2023-06-27 17:48:02",
                    "tz_name": "UTC+01",
                    "update_by": 293382,
                    "update_at": "2023-06-27 17:48:02",
                    "vc": "289",
                    "init_soft_ver": "V00.00.06",
                    "init_hard_ver": "H12.02.02",
                    "init_rf_soft_ver": "256",
                    "init_rf_hard_ver": "0",
                    "wifi_ver": null,
                    "model_info": null,
                    "repeater_num": 0,
                    "mi_num": 5,
                    "rule": {
                        "dev_type": 1,
                        "version": 3,
                        "balance": 1,
                        "reflux": 1,
                        "repeater": 0,
                        "module_count": 99,
                        "multiple": 0,
                        "sun_spec": 0,
                        "power_limit": 7,
                        "model": 0,
                        "module_no": "HD-Insight",
                        "module": "HD-Insight",
                        "mi_list": [
                            "A21",
                            "A11",
                            "A22",
                            "A01",
                            "A12",
                            "A23",
                            "A02",
                            "A13",
                            "A03",
                            "A15",
                            "A05"
                        ],
                        "sub1g": 0,
                        "rule_config": 1,
                        "conn_way": 11,
                        "inner": 0,
                        "pv": 0,
                        "series": 0,
                        "es": 0,
                        "au": 0,
                        "hp": 0,
                        "lc": 0,
                        "ble": 0,
                        "data_interval": 0,
                        "scan": 0,
                        "classify": 1,
                        "map": {
                            "ut5": 99
                        },
                        "rep_set": [],
                        "un": 0,
                        "gen": 0
                    },
                    "fm": {}
                }
        """
        return self._all_data