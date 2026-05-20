"""Service for retrieving detailed information about a single microinverter.
 
This module provides :class:`MySolensoMicroFind`, which wraps the
``micro_find`` Solenso endpoint. A valid microinverter ID must be set via
:meth:`~MySolensoMicroFind.set_micro` before data is fetched.  The ID is
validated against the list returned by
:class:`~mysolenso.services.dtu.selectall.MySolensoDTUSelectAll`.
"""
 
from __future__ import annotations
 
import logging
from typing import Any
 
from ...post import MySolensoPost
from ...const import API_MICRO_FIND
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoMicroFind:
    """Retrieve the full detail record for a single microinverter.
 
    Call :meth:`set_micro` with a valid microinverter ID to trigger the API
    request and populate the cached data.
 
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
        self._micro_id = None
 
 
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
    # Micro selection
    # ------------------------------------------------------------------
 
    def set_micro(self, id: int, refresh: bool = True) -> None:
        """Select the microinverter to query and optionally fetch its data.
 
        The microinverter ID is validated against the list returned by
        :meth:`~mysolenso.services.dtu.selectall.MySolensoDTUSelectAll.list_micros`.
 
        Args:
            id (int): Internal numeric ID of the microinverter to query.
            refresh (bool): When ``True`` (default), immediately fetches the
                microinverter detail record from the API.
 
        Raises:
            MySolensoException: If the requested microinverter ID is not found.
        """
        
        self.parent.dtuselectall.dtu_select_all_refresh()
        micros = self.parent.dtuselectall.list_micros
 
        # Verify the requested micro ID exists in the account.
        if not any(micro.get("id") == id for micro in micros):
            msg = (
                f"{self.__class__.__name__} - set_micro: "
                f"micro {id} not found."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)
 
        self._micro_id = id
 
        # Reload data for the new micro unless the caller deferred it.
        if refresh:
            self._get_micro_find()
            
            
    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------
 
    def _get_micro_find(self) -> None:
 
        try:
            
            if self._micro_id is None:
                msg = (
                    f"{self.__class__.__name__} - _get_micro_find: "
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
                    "id": self._micro_id},
                "WAITING_PROMISE": True
            })
            response = self._client.post(API_MICRO_FIND)
 
            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_micro_find: "
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
 
    def micro_find_refresh(self) -> None:
        """Force a fresh fetch of the microinverter detail record from the API."""
        self._get_micro_find()
 
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
 
    @property
    def all_data(self) -> dict:
        """Raw API response for the microinverter find endpoint.
 
        Returns:
            dict: Full microinverter record including serial number, firmware
            versions, hardware model, port configuration, parent DTU reference,
            and connection/warning status. Example::
 
                {
                    "sn": "A11001X4A",
                    "warn_data": {"warn": False, "connect": True},
                    "id": 7454520,
                    "sid": 1553580,
                    "station_name": "DOE JOHN",
                    "dev_type": 3,
                    "tz_name": "UTC+01",
                    "vc": "2L2",
                    "init_soft_ver": "V01.00.04",
                    "init_hard_no": "Sol-H1000H",
                    "init_hard_ver": "H00.04.00",
                    "dtu_id": 1456060,
                    "dtu_sn": "D0100289H",
                    "rule": {"port": 2, "phase": 1, "series": 7, ...},
                    ...
                }
        """
        return self._all_data