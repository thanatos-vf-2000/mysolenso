from __future__ import annotations

import logging
from typing import Any

from ...post import MySolensoPost
from ...const import API_MICRO_FIND
from ...exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoMicroFind:

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

        self.parent.dtuselectall.dtu_select_all_refresh()
        micros = self.parent.dtuselectall.list_micros

        # Verify the requested station ID exists in the account.
        if not any(micro.get("id") == id for micro in micros):
            msg = (
                f"{self.__class__.__name__} - set_micro: "
                f"micro {id} not found."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._micro_id = id

        # Reload data for the new station unless the caller deferred it.
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

        self._get_micro_find()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        """_summary_

        Returns:
            {
                "sn": "A11001X4A",
                "warn_data": {
                    "warn": false,
                    "connect": true
                },
                "id": 7454520,
                "sid": 1553580,
                "classify": 1,
                "station_name": "DOE JOHN",
                "station_city_code": "FR13005000000000",
                "dev_type": 3,
                "replace_num": 0,
                "grid_id": 0,
                "grid_name": "",
                "grid_version": "",
                "create_by": 293382,
                "create_at": "2023-08-05 10:57:22",
                "tz_name": "UTC+01",
                "update_by": 293382,
                "update_at": "2023-08-05 10:57:22",
                "port_num": null,
                "port_array": null,
                "vc": "2L2",
                "init_soft_ver": "V01.00.04",
                "init_hard_no": "Sol-H1000H",
                "init_hard_ver": "H00.04.00",
                "dtu_id": 1456060,
                "dtu_sn": "D0100289H",
                "dtu_version": 3,
                "repeater_id": null,
                "repeater_sn": null,
                "layout_list": [],
                "rule": {
                    "dev_type": 3,
                    "port": 2,
                    "version": 3,
                    "phase": 1,
                    "hm": 1,
                    "inner": 0,
                    "ctl_mode": 3,
                    "exc": 0,
                    "grid_type": 0,
                    "map": {},
                    "ble": 0,
                    "series": 7
                }
            }
        """
        return self._all_data
