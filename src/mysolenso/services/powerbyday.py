"""MySolenso intra-day power curve service.

Provides the :class:`MySolensoPowerByDay` class, which queries the
``/count_power_by_day`` Hoymiles endpoint and parses the binary protobuf
response to expose a time-indexed dictionary of grid power measurements
(in Watts) for a single day.

By default the service loads data for **today** (or yesterday if the local
hour is before 01:00, to avoid an empty dataset at midnight).  Use
:meth:`~MySolensoPowerByDay.set_day` to query any historical date.

This module is instantiated automatically by :class:`~mysolenso.MySolenso`
and accessible via ``client.powerbyday``.

Example:
    ::

        client = MySolenso(username="user", token="tok")

        result = client.powerbyday.get_data
        print(result["date"])              # "2026-05-22"
        print(result["metric"])            # "grid_power"
        print(result["values"]["08:30"])   # e.g. 1523.5  (W)

        # Query a specific date
        client.powerbyday.set_day("2026-01-01")
        result = client.powerbyday.get_data
"""

from __future__ import annotations

import logging
import re
import struct
from datetime import datetime, timedelta
from typing import Dict, Optional

from ..post import MySolensoPost
from ..const import API_POWER_BY_DAY
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoPowerByDay:
    """Intra-day grid power curve for a single PV station.

    Parses the binary protobuf response from ``/count_power_by_day`` and
    exposes a structured result containing the date, the metric name
    (``"grid_power"``), and a ``{HH:MM: float}`` dictionary of power
    measurements in Watts sampled throughout the day.

    Args:
        parent: Instance of :class:`~mysolenso.MySolenso` providing access
            to the ``auth`` and ``station`` sub-modules.

    Raises:
        MySolensoException: If ``parent.station.station_id`` is ``None``,
            if ``grid_power`` marker is absent from the response, or if any
            network or parsing error occurs.

    Attributes:
        parent: Reference to the parent :class:`~mysolenso.MySolenso` object.

    Note:
        If the local clock hour is before ``01:00``, the service
        automatically loads **yesterday's** data to avoid returning an
        empty intra-day curve at midnight.

    Example:
        ::

            client = MySolenso(username="admin", token="tok")
            pb = client.powerbyday

            print(pb.get_data["date"])              # "2026-05-22"
            print(pb.get_data["metric"])            # "grid_power"
            print(pb.get_data["values"]["10:00"])   # 2048.75  (W)
    """

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

        self._get_power_by_day()

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_power_by_day(self) -> None:
        """Query the API and parse the binary protobuf response for one day.

        The response is a binary protobuf payload containing:

        - **Time labels** - ``HH:MM`` strings, one per measurement interval.
        - **Date label** - a ``YYYY-MM-DD`` string confirming the queried day.
        - **grid_power field** - a packed ``repeated float32`` array
          (little-endian) prefixed by a 3-byte protobuf header
          (``grid_power`` marker + ``0x12`` tag + 2-byte length varint).

        Parsing strategy:

        - Times are extracted with a regex (``\\d{2}:\\d{2}``).
        - The date is extracted with a regex (``\\d{4}-\\d{2}-\\d{2}``).
        - The ``grid_power`` marker is located; the float array starts
          3 bytes after the marker end (1 tag byte + 2 length bytes).
        - The array ends at the ``\\x1a\\x0a`` delimiter that precedes the
          date field in the protobuf message.
        - Float32 values are decoded in 4-byte aligned chunks; times and
          values are zipped into the ``values`` dictionary.

        Raises:
            MySolensoException: If ``grid_power`` is absent from the
                response, or if any network or struct unpacking error occurs.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_hoymiles())
            self._client.set_raw_payload({"sid": self._station_id, "date": self._day})
            response: bytes = self._client.poststr(API_POWER_BY_DAY)

            # ----------------------------------------------------------
            # 1. Extract HH:MM time labels
            # ----------------------------------------------------------
            times = [t.decode() for t in re.findall(rb'(\d{2}:\d{2})', response)]

            # ----------------------------------------------------------
            # 2. Extract the date string
            # ----------------------------------------------------------
            date_match = re.search(rb'(\d{4}-\d{2}-\d{2})', response)
            date_value: Optional[str] = (
                date_match.group(1).decode() if date_match else None
            )

            # ----------------------------------------------------------
            # 3. Locate the grid_power protobuf field
            # ----------------------------------------------------------
            marker = b'grid_power'
            idx = response.find(marker)
            if idx == -1:
                raise MySolensoException("'grid_power' marker not found in response.")

            # Float array starts 3 bytes after the marker
            # (1 byte field tag 0x12 + 2 bytes length varint)
            start = idx + len(marker) + 3

            # ----------------------------------------------------------
            # 4. Find the end of the float array (date delimiter)
            # ----------------------------------------------------------
            date_delimiter = b'\x1a\x0a'
            end = response.find(date_delimiter)
            if end == -1:
                end = len(response)

            binary_part = response[start:end]

            # ----------------------------------------------------------
            # 5. Decode float32 values (4-byte aligned)
            # ----------------------------------------------------------
            floats = []
            for i in range(0, len(binary_part) - 3, 4):
                chunk = binary_part[i:i + 4]
                if len(chunk) == 4:
                    floats.append(round(struct.unpack('<f', chunk)[0], 2))

            # ----------------------------------------------------------
            # 6. Build the result structure
            # ----------------------------------------------------------
            self._result = {
                "metric": "grid_power",
                "date":   date_value,
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
            self._get_power_by_day()

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

                client.powerbyday.set_day("2026-05-22")
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
                self._get_power_by_day()

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
        self._get_power_by_day()
        
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def get_data(self) -> dict:
        """Intra-day power curve for the active station and date.
        
        Example:
        {
            'metric': 'grid_power',
            'date': '2026-05-22',
            'values': {'00:00': 0.0, '01:00': 0.0, '02:00': 0.0, '03:00': 0.0, '04:00': 0.0, '05:00': 0.0, '06:00': 0.0, '06:30': 42.6, '06:45': 71.6, '07:00': 108.3, '07:15': 114.9, '07:30': 199.4, '07:45': 161.2, '08:00': 139.6, '08:15': 257.2, '08:30': 501.9, '08:45': 743.0, '09:00': 784.7, '09:15': 881.3, '09:30': 1259.3, '09:45': 929.3, '10:00': 1225.9, '10:15': 1416.0, '10:30': 1535.7, '10:45': 1131.0, '11:00': 1917.1, '11:15': 2750.5, '11:30': 1542.4, '11:45': 1220.3, '12:00': 2245.9, '12:15': 3135.0, '12:30': 2582.1, '12:45': 1930.6, '13:00': 4368.4, '13:15': 3474.5, '13:30': 1516.8, '13:45': 2436.1, '14:00': 3371.3, '14:15': 1513.3, '14:30': 1891.5, '14:45': 1967.2, '15:00': 1906.7, '15:15': 2066.9, '15:30': 1863.2, '15:45': 4957.9, '16:00': 4360.8, '16:15': 4118.8, '16:30': 3748.1, '16:45': 926.6, '17:00': 1326.0, '17:15': 1702.5, '17:30': 1394.9, '17:45': 1063.7, '18:00': 645.2, '18:15': 2089.5, '18:30': 241.0, '18:45': 549.7, '19:00': 686.4, '19:15': 583.5, '19:30': 567.7, '19:45': 434.7, '20:00': 436.8, '20:15': 426.4, '20:30': 389.6, '20:45': 177.9, '21:00': 56.4, '21:15': 20.8, '22:15': 0.0, '23:15': 0.0}
        }
        
        Returns a dictionary with three keys:

        - ``"metric"`` *(str)* - always ``"grid_power"``.
        - ``"date"``   *(str | None)* - queried date in ``YYYY-MM-DD``
          format as confirmed by the API, or ``None`` if absent.
        - ``"values"`` *(Dict[str, float])* - ``{HH:MM: watts}`` mapping
          of sampled grid power readings throughout the day.

        Returns:
            dict: Structured result with ``metric``, ``date``, and
            ``values`` keys.

        Example:
            ::

                data = client.powerbyday.get_data
                # {
                #   "metric": "grid_power",
                #   "date":   "2026-05-22",
                #   "values": {"08:00": 512.0, "08:30": 1024.5, ...}
                # }
                print(data["values"].get("12:00", 0))
        """
        return self._result
