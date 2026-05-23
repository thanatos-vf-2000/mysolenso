from __future__ import annotations

import logging
import re
import struct
from datetime import datetime, timedelta
from typing import Dict, Optional

from ...post import MySolensoPost
from ...const import API_POWER_PLAYBACK_BY_DAY
from ...exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoPowerPlayBackByDay:
    
    def __init__(self, parent) -> None:
        self.parent = parent

        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = self.parent.station.station_id

        # Default to today; use yesterday before 01:00 to avoid empty data
        now = datetime.now()
        if now.hour < 1:
            self._day = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            self._day = now.strftime("%Y-%m-%d")


    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_power_playback_by_day(self) -> None:

        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_hoymiles())
            self._client.set_raw_payload({"sid": self._station_id, "date": self._day})
            response: bytes = self._client.poststr(API_POWER_PLAYBACK_BY_DAY)

            # ----------------------------------------------------------
            # 1. Date
            # ----------------------------------------------------------
            date_match = re.search(rb'(\d{4}-\d{2}-\d{2})', response)
            date_value: Optional[str] = (
                date_match.group(1).decode() if date_match else None
            )

            # ----------------------------------------------------------
            # 2. Time labels (protobuf 0x12 + len + string)
            # ----------------------------------------------------------
            times = [
                t.decode()
                for t in re.findall(rb'(\d{2}:\d{2})', response)
            ]

            # ----------------------------------------------------------
            # 3. Locate float block start (after last time occurrence)
            # ----------------------------------------------------------
            last_time = times[-1].encode() if times else None

            if not last_time:
                raise ValueError("No time values found")

            start = response.rfind(last_time) + len(last_time)

            # skip protobuf padding until first float-like region
            while start < len(response) and response[start] not in b'\x00\xcd\x9a\x3f\x40\x41\x42\x43\x44\x45':
                start += 1

            binary_part = response[start:]

            # ----------------------------------------------------------
            # 4. Extract float32 safely (stop on garbage pattern)
            # ----------------------------------------------------------
            floats = []

            for i in range(0, len(binary_part) - 3, 4):
                chunk = binary_part[i:i + 4]

                # stop heuristic: too many ASCII control bytes
                if chunk in [b'<<<<', b'\x0f\x0f\x0f\x0f']:
                    break

                try:
                    value = struct.unpack('<f', chunk)[0]
                    floats.append(round(value, 2))
                except struct.error:
                    break

            # ----------------------------------------------------------
            # 5. Build result
            # ----------------------------------------------------------
            self._result = {
                "date": date_value,
                "values": dict(zip(times, floats)),
            }

        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                f"Failed to parse power-by-day response: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Station and date selection
    # ------------------------------------------------------------------

    def set_station_id(self, id: int, refresh: bool = True) -> None:
        """Switch the active station and optionally reload the power curve.

        Args:
            id (int): Station ID to activate. Must exist in the account's
                station list.
            refresh (bool): If ``True`` (default), immediately reloads data
                for the new station. Set to ``False`` to defer the call.

        Raises:
            MySolensoException: If ``id`` is not found in the account's
                station list, or if the subsequent API call fails.

        Example:
            ::

                client.powerbyday.set_station_id(43)
                print(client.powerbyday.get_data["values"])
        """
        stations = self.parent.station.stations
        if not any(station.get("id") == id for station in stations):
            msg = (
                f"{self.__class__.__name__} - set_station_id: "
                f"station {id} not found."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = id
        if refresh:
            self._get_power_playback_by_day()

    def set_day(self, day: str, refresh: bool = True) -> None:
        """Set the queried date and optionally reload the power curve.

        Args:
            day (str): Date string in ``YYYY-MM-DD`` format. Must be between
                ``1900-01-01`` and today (inclusive).
            refresh (bool): If ``True`` (default), immediately reloads data
                for the new date. Set to ``False`` to defer the call.

        Raises:
            MySolensoException: If ``day`` is not in ``YYYY-MM-DD`` format,
                is outside the allowed range, or if the API call fails.

        Example:
            ::

                client.powerbyday.set_day("2025-12-25")
                print(client.powerbyday.get_data["values"])
        """
        try:
            if len(day) != 10:
                raise ValueError("Invalid length.")

            date_obj = datetime.strptime(day, "%Y-%m-%d").date()

            min_date = datetime(1900, 1, 1).date()
            max_date = datetime.now().date()

            if not (min_date <= date_obj <= max_date):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"date outside the allowed range "
                    f"{min_date} <= {date_obj} <= {max_date}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            self._day = day
            if refresh:
                self._get_power_playback_by_day()

        except MySolensoException:
            raise
        except ValueError:
            msg = (
                f"{self.__class__.__name__} - set_day: "
                f"'{day}' is not a valid YYYY-MM-DD date."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

    # ------------------------------------------------------------------
    # Refresh Power data
    # ------------------------------------------------------------------
    def get_power_refresh(self) -> None:
        """Query the API for refresh Power energy data.
        """
        self._get_power_playback_by_day()
        
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
    @property
    def day(self) -> str:
        return  self._day
        
    @property
    def get_data(self) -> dict:
        """

        Returns:
            dict: _description_
            {'date': '2026-05-23', 'values': {'00:00': 0.0, '01:00': 0.0, '02:00': 0.0, '03:00': 0.0, '04:00': 0.0, '05:00': 0.0, '06:00': 26.6, '06:15': 63.4, '06:30': 110.3, '06:45': 151.1, '07:00': 173.7, '07:15': 214.8, '07:30': 271.9, '07:45': 312.2, '08:00': 401.8, '08:15': 409.8, '08:30': 443.3, '08:45': 612.9, '09:00': 809.4, '09:15': 1021.3, '09:30': 1201.7, '09:45': 1260.7, '10:00': 1640.1, '10:15': 1843.1, '10:30': 1763.1, '10:45': 2126.9, '11:00': 2475.3, '11:15': 2485.1}}
        """
        return self._result
