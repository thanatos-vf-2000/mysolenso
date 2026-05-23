"""Station panel layout service for MySolenso.

This module provides :class:`MySolensoStationLayout`, which retrieves the physical
placement of every microinverter panel for the active station.  Each record
returned by the API describes one panel port and includes the DTU it is attached
to, the microinverter serial number, and the (x, y) grid coordinates of the panel
in the installation diagram.
"""
from __future__ import annotations
 
import logging
from typing import Any
 
from ...post import MySolensoPost
from ...const import API_STATION_LAYOUT
from ...exceptions import MySolensoException
 
_LOG = logging.getLogger(__name__)
 
 
class MySolensoStationLayout:
    """Retrieve the physical panel layout for the active Solenso station.

    Wraps the :data:`~mysolenso.const.API_STATION_LAYOUT` endpoint and exposes
    panel placement records grouped by DTU.  Call :meth:`station_layout_refresh`
    before accessing any property for the first time.

    Args:
        parent: The :class:`~mysolenso.mysolenso.MySolenso` facade instance that
            holds the active session (``parent.auth``) and station context
            (``parent.station``).

    Raises:
        MySolensoException: If no station has been selected on the parent
            (``parent.station.station_id`` is ``None``).
    """

    def __init__(self, parent) -> None:
        """Initialise the layout service and validate the station context.

        Args:
            parent: The :class:`~mysolenso.mysolenso.MySolenso` facade instance.

        Raises:
            MySolensoException: If ``parent.station.station_id`` is ``None``.
        """
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
        """Fetch the panel layout from the API and cache the result.

        Sends a POST request to :data:`~mysolenso.const.API_STATION_LAYOUT` and
        stores the raw response list in ``self._all_data``.

        Raises:
            MySolensoException: On an empty/null response or any network/parse error.
        """
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
                    "aid": 270901,
                    "dtu_id": 1238090,
                    "dtu_sn": "D0900999H",
                    "dev_type": 3,
                    "mi_id": 9988940,
                    "mi_sn": "A900016B4",
                    "port": 1,
                    "x": 0,
                    "y": 8
                },
                {
                    "id": 8967082,
                    "aid": 270901,
                    "dtu_id": 1238090,
                    "dtu_sn": "D0900999H",
                    "dev_type": 3,
                    "mi_id": 9988940,
                    "mi_sn": "A900016B4",
                    "port": 2,
                    "x": 0,
                    "y": 9
                },
                {
                    "id": 8967077,
                    "aid": 270901,
                    "dtu_id": 1238090,
                    "dtu_sn": "D0900999H",
                    "dev_type": 3,
                    "mi_id": 9988910,
                    "mi_sn": "A900016B3",
                    "port": 1,
                    "x": 0,
                    "y": 4
                },
                {
                    "id": 8967078,
                    "aid": 270901,
                    "dtu_id": 1238090,
                    "dtu_sn": "D0900999H",
                    "dev_type": 3,
                    "mi_id": 9988910,
                    "mi_sn": "A900016B3",
                    "port": 2,
                    "x": 0,
                    "y": 5
                },
                {
                    "id": 8967073,
                    "aid": 270901,
                    "dtu_id": 1238090,
                    "dtu_sn": "D0900999H",
                    "dev_type": 3,
                    "mi_id": 9988920,
                    "mi_sn": "A900016B1",
                    "port": 1,
                    "x": 0,
                    "y": 0
                },
                {
                    "id": 8967074,
                    "aid": 270901,
                    "dtu_id": 1238090,
                    "dtu_sn": "D0900999H",
                    "dev_type": 3,
                    "mi_id": 9988920,
                    "mi_sn": "A900016B1",
                    "port": 2,
                    "x": 0,
                    "y": 1
                },
                {
                    "id": 8967075,
                    "aid": 270901,
                    "dtu_id": 1238090,
                    "dtu_sn": "D0900999H",
                    "dev_type": 3,
                    "mi_id": 9988930,
                    "mi_sn": "A900016B2",
                    "port": 1,
                    "x": 0,
                    "y": 2
                },
                {
                    "id": 8967076,
                    "aid": 270901,
                    "dtu_id": 1238090,
                    "dtu_sn": "D0900999H",
                    "dev_type": 3,
                    "mi_id": 9988930,
                    "mi_sn": "A900016B2",
                    "port": 2,
                    "x": 0,
                    "y": 3
                }]
        """
        return self._all_data
 
    @property
    def list_dtu(self) -> list[dict]:
        """Return a deduplicated list of DTUs referenced in the layout.

        Returns:
            list[dict]: Each entry has the keys ``dtu_id`` (int) and
            ``dtu_sn`` (str). Duplicate DTU ids are collapsed to a single entry.

        Raises:
            ValueError: If :attr:`all_data` has not been populated yet.
        """
        data_list = self._all_data
 
        # Guard against an uninitialised or empty data store.
        if not data_list:
            raise ValueError("all_data is missing or empty")
 
        seen_dtu_ids = set()
        result = []

        for item in data_list:
            dtu_id = item["dtu_id"]

            # Skip duplicate DTU ids.
            if dtu_id in seen_dtu_ids:
                continue

            seen_dtu_ids.add(dtu_id)

            result.append({
                "dtu_id": item["dtu_id"],
                "dtu_sn": item["dtu_sn"]
            })

        return result
    
    def list_dtu_ids(self) -> list[int]:
        """Return a list of unique DTU ids found in the layout data.

        Returns:
            list[int]: Unique DTU ids. Order is not guaranteed.

        Raises:
            ValueError: If :attr:`all_data` has not been populated yet.
        """
        if not self._all_data:
            raise ValueError("all_data is missing or empty")

        return list({item["dtu_id"] for item in self._all_data})
    
    @property
    def list_micro_all(self) -> list[dict]:
        """Return a deduplicated list of microinverters referenced in the layout.

        Returns:
            list[dict]: Each entry has the keys ``id`` (int), ``sn`` (str), and
            ``port_dtu`` (int). Duplicate microinverter ids are collapsed to a
            single entry.

        Raises:
            ValueError: If :attr:`all_data` has not been populated yet.
        """
        data_list = self._all_data
 
        # Guard against an uninitialised or empty data store.
        if not data_list:
            raise ValueError("all_data is missing or empty")
 
        seen_micro_ids = set()
        result = []

        for item in data_list:
            micro_id = item["dtu_id"]

            # Skip duplicate microinverter ids.
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
        """Return all panel records attached to a given DTU, sorted by position.

        Args:
            dtu_id (int): The DTU id to filter on.

        Returns:
            list[dict]: Panel records for the requested DTU, each containing
            ``id``, ``sn``, ``port``, ``x``, and ``y``. The list is sorted
            by ``(x, y)`` ascending.

        Raises:
            ValueError: If :attr:`all_data` has not been populated yet.
        """
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