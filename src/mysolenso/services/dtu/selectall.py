"""Service for retrieving the DTU and associated microinverter list.
 
This module provides :class:`MySolensoDTUSelectAll`, which wraps the
``dtu_select_all`` Solenso endpoint. One call returns the primary DTU record
and the complete list of microinverters attached through the repeater layer.
"""
 
from __future__ import annotations
 
import logging
from typing import Any
 
from ...post import MySolensoPost
from ...const import API_DTU_SELECT_ALL
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoDTUSelectAll:
    """Retrieve the DTU and all associated microinverters for a station.
 
    Call :meth:`dtu_select_all_refresh` to populate the data, then access
    the properties below.  The active station is inherited from the parent
    :class:`~mysolenso.mysolenso.MySolenso` object; use :meth:`set_station`
    to query a different station without rebuilding the whole client.
 
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
 
 
    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------
 
    def set_station(self, id: int, refresh: bool = True) -> None:
        """Switch the active station for DTU queries.
 
        Args:
            id (int): ID of the target station. Must exist in the account's
                station list.
            refresh (bool): When ``True`` (default), immediately re-fetches
                the DTU data for the new station.
 
        Raises:
            MySolensoException: If the requested station ID is not found in the
                account.
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
            self._get_dtu_select_all()
 
 
    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------
 
    def _get_dtu_select_all(self) -> None:
 
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
            response = self._client.post(API_DTU_SELECT_ALL)
 
            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_dtu_select_all: "
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
            self._dtu_id       = _clean(self._all_data.get("dtu").get("id"))
            self._dtu_sn       = _clean(self._all_data.get("dtu").get("sn"))
            self._dtu_dev_type = _clean(self._all_data.get("dtu").get("dev_type"))
            self._dtu_vc       = _clean(self._all_data.get("dtu").get("vc"))
            self._micros       = _clean(self._all_data.get("repeater_list")[0].get("micros"))
 
 
 
        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc
 
    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
 
    def dtu_select_all_refresh(self) -> None:
        """Force a fresh fetch of the DTU and microinverter data from the API.
 
        Equivalent to calling :meth:`_get_dtu_select_all` directly.
        Use this method to update the cached data without switching station.
        """
        self._get_dtu_select_all()
 
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
 
    @property
    def all_data(self) -> dict:
        """Raw API response for the DTU select-all endpoint.
 
        Returns:
            dict: Full response dictionary containing the ``dtu`` record and the
            ``repeater_list`` with its nested ``micros`` list. Example::
 
                {
                    "dtu": {
                        "id": 1456060,
                        "sn": "D0100289H",
                        "dev_type": 1,
                        "vc": "289"
                    },
                    "repeater_list": [
                        {
                            "id": 0,
                            "sn": "",
                            "dev_type": 2,
                            "inv_id": null,
                            "inv_sn": null,
                            "inv_type": null,
                            "micros": [
                                {
                                    "sn": "A110016B1",
                                    "id": 6654220,
                                    "vc": "2BD",
                                    "dev_type": 3,
                                    "port_array": [
                                        1,
                                        2
                                    ]
                                },
                                {
                                    "sn": "A110016GV",
                                    "id": 6654230,
                                    "vc": "23D",
                                    "dev_type": 3,
                                    "port_array": [
                                        1,
                                        2
                                    ]
                                },
                                {
                                    "sn": "A110016L3",
                                    "id": 6654210,
                                    "vc": "212",
                                    "dev_type": 3,
                                    "port_array": [
                                        1,
                                        2
                                    ]
                                },
                                {
                                    "sn": "A110016VJ",
                                    "id": 6654200,
                                    "vc": "22L",
                                    "dev_type": 3,
                                    "port_array": [
                                        1,
                                        2
                                    ]
                                },
                                {
                                    "sn": "A11001X4A",
                                    "id": 7454520,
                                    "vc": "2L2",
                                    "dev_type": 3,
                                    "port_array": [
                                        1,
                                        2
                                    ]
                                }
                            ]
                        }
                    ]
                }
        """
        return self._all_data
 
    @property
    def dtu_id(self) -> int:
        """Internal numeric ID of the primary DTU."""
        return self._dtu_id
 
    @property
    def dtu_sn(self) -> str:
        """Serial number of the primary DTU (e.g. ``"D0100289H"``)."""
        return self._dtu_sn
 
    @property
    def dtu_dev_type(self) -> int:
        """Device type code of the primary DTU (``1`` for a standard DTU)."""
        return self._dtu_dev_type
 
    @property
    def dtu_vc(self) -> str:
        """Firmware version code of the primary DTU (e.g. ``"289"``)."""
        return self._dtu_vc
 
    @property
    def list_micros_info(self) -> list[dict]:
        """Full microinverter records attached to the DTU.
 
        Returns:
            list[dict]: Each item contains ``sn``, ``id``, ``vc``,
            ``dev_type``, and ``port_array`` for one microinverter. Example::
 
                [
                    {"sn": "A110016B1", "id": 6654220, "vc": "2BD",
                     "dev_type": 3, "port_array": [1, 2]},
                    ...
                ]
        """
        return self._micros
    
    @property
    def list_micros(self) -> list[dict]:
        """Minimal microinverter projection: serial number and internal ID only.
 
        Returns:
            list[dict]: Each item contains only ``sn`` and ``id``. Example::
 
                [
                    {"sn": "A110016B1", "id": 6654220},
                    {"sn": "A110016GV", "id": 6654230},
                    ...
                ]
 
        Raises:
            ValueError: If the internal data store is uninitialised or empty
                (i.e. :meth:`dtu_select_all_refresh` has not been called yet).
        """
        data_list = self._micros
 
        # Guard against an uninitialised or empty data store.
        if not data_list:
            raise ValueError("all_data is missing or empty")
 
        # Return a minimal projection: date + pv_eq only.
        return [
            {
                "sn"   : item["sn"],
                "id"   : item["id"]
            }
            for item in data_list
        ]