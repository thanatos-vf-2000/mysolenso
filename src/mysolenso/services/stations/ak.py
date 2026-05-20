from __future__ import annotations

import logging
from typing import Any

from ...post import MySolensoPost
from ...const import API_STATION_AK
from ...exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoStationAK:

    def __init__(self, parent) -> None:
        self.parent = parent

        # Validate that a station has already been selected by the parent.
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = self.parent.station.station_id
        self._station_ak = self.parent.station.ak


    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------

    def set_station(self, id: int, ak: str, refresh: bool = True) -> None:

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
        self._station_ak = ak

        # Reload data for the new station unless the caller deferred it.
        if refresh:
            self._get_station_ak()


    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_station_ak(self) -> None:

        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())

            # Build the request body: station list, mode, and date range.
            # Note: no pagination — this endpoint returns a single aggregate.
            self._client.set_raw_payload({
                "ERROR_BACK": True,
                "body": {
                    "sid": self._station_id,
                    "ak": self._station_ak
                },
                "WAITING_PROMISE": True
            })
            response = self._client.post(API_STATION_AK)

            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_station_ak: "
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
            self._id          = _clean(self._all_data.get("id"))
            self._longitude          = _clean(self._all_data.get("longitude"))
            self._latitude      = _clean(self._all_data.get("latitude"))
            self._address        = _clean(self._all_data.get("address"))

        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def station_ak_refresh(self) -> None:

        self._get_station_ak()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        """_summary_

        Returns:
            {
                "id": 1553580,
                "longitude": "39.10884652257048",
                "latitude": "-76.77128918829347",
                "address": "95 Moon Road, 99999 Galaxy, World"
            }
        """
        return self._all_data

    @property
    def id(self) -> int:
        return self._id
    
    @property
    def longitude(self) -> str:
        return self._longitude
    
    @property
    def latitude(self) -> str:
        return self._latitude
        
    @property
    def address(self) -> str:
        return self._address