"""MySolenso daily PV energy production service.

Provides the :class:`MySolensoCountByDayOfYeay` class, which queries the
``/power_day_of_year`` endpoint and parses the binary protobuf response to
expose a ``{date: energy_Wh}`` dictionary covering every day since the
station was commissioned.

The API returns a mixed response:

- A UTF-8 text section listing dates in ``YYYY-MM-DD`` format (one per line).
- A binary protobuf section containing a ``pv_eq`` field encoded as a
  packed ``repeated float`` (little-endian float32, wire type 2).

Both sections are parsed and zipped together to build the final mapping.

Example:
    ::

        client = MySolenso(username="user", token="tok")

        data = client.day_of_year.get_data
        print(data["2026-01-01"])   # e.g. 3241.5 (Wh)

        # Switch station and refresh
        client.day_of_year.set_station_id(43)
        data = client.day_of_year.get_data
"""

from __future__ import annotations

import logging
import re
import struct
from typing import Dict

from ..post import MySolensoPost
from ..const import API_POWER_DAY_OF_YEAR
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoCountByDayOfYeay:
    """Daily PV energy production indexed by date for a single station.

    Parses the binary protobuf response from ``/power_day_of_year`` and
    exposes a ``{YYYY-MM-DD: float}`` dictionary where each value is the
    daily energy production in Wh.

    Days with no production (e.g. the current day before sunset, or cloudy
    days) are included with a value of ``0.0`` rather than being silently
    dropped.

    Args:
        parent: Instance of :class:`~mysolenso.MySolenso` providing access
            to the ``auth`` and ``station`` sub-modules.

    Raises:
        MySolensoException: If ``parent.station.station_id`` is ``None``,
            or if parsing the response fails.

    Attributes:
        parent: Reference to the parent :class:`~mysolenso.MySolenso` object.

    Example:
        ::

            client = MySolenso(username="admin", token="tok")
            doy = client.day_of_year

            print(doy.get_data["2025-07-14"])  # 18432.0 Wh
            print(len(doy.get_data))           # number of days covered
    """

    def __init__(self, parent) -> None:
        self.parent = parent

        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = self.parent.station.station_id
        self._get_count_by_day_of_year()

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_count_by_day_of_year(self) -> None:
        """Query the API and parse the binary protobuf response.

        The response is a mixed text/binary payload:

        1. **Text section** - one ``YYYY-MM-DD`` date per line, covering
           every day from the station's first production to today.
        2. **Binary section** - a protobuf message containing a ``pv_eq``
           field (field 2, wire type 2) encoding a packed array of
           little-endian ``float32`` values, one per date.

        Parsing strategy:

        - Dates are extracted with a regex (``\\d{4}-\\d{2}-\\d{2}``).
        - The ``pv_eq`` marker is located in the raw bytes.
        - The protobuf field tag (``0x12``) and varint length are decoded to
          find the exact start and byte-length of the float array.
        - ``struct.unpack`` reads exactly ``length // 4`` float32 values in
          one aligned pass - **no byte-by-byte scanning, no value filtering**.
        - Dates and values are zipped into a dictionary; unmatched trailing
          values (protobuf padding zeros) are silently ignored.

        Raises:
            MySolensoException: If the ``pv_eq`` marker is absent, if the
                protobuf header is malformed, or if any network/HTTP error
                occurs.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_hoymiles())
            self._client.set_raw_payload({"sid": self._station_id})
            response: bytes = self._client.poststr(API_POWER_DAY_OF_YEAR)

            # ----------------------------------------------------------
            # 1. Extract dates from the text section
            # ----------------------------------------------------------
            dates = [
                d.decode()
                for d in re.findall(rb'\d{4}-\d{2}-\d{2}', response)
            ]

            if not dates:
                raise MySolensoException("No dates found in the API response.")

            # ----------------------------------------------------------
            # 2. Locate the pv_eq protobuf field
            # ----------------------------------------------------------
            marker = b'pv_eq'
            idx = response.find(marker)
            if idx == -1:
                raise MySolensoException("'pv_eq' marker not found in response.")

            pos = idx + len(marker)

            # ----------------------------------------------------------
            # 3. Decode the protobuf header (field tag + varint length)
            #
            # Expected layout after "pv_eq":
            #   0x12            → field 2, wire type 2 (length-delimited)
            #   <varint>        → byte-length of the packed float array
            #   <float32...>    → little-endian IEEE-754 values
            # ----------------------------------------------------------
            if response[pos] != 0x12:
                raise MySolensoException(
                    f"Unexpected protobuf tag: {response[pos]:#x} (expected 0x12)."
                )
            pos += 1

            # Decode the varint length (LEB128, 7 bits per byte)
            byte_length = 0
            shift = 0
            while True:
                if pos >= len(response):
                    raise MySolensoException("Truncated varint in protobuf header.")
                b = response[pos]; pos += 1
                byte_length |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7

            # ----------------------------------------------------------
            # 4. Decode float32 array in a single aligned pass
            #
            # This avoids the previous byte-by-byte sliding-window
            # approach which dropped zeros (days with 0 Wh production)
            # and generated spurious values from overlapping bytes.
            # ----------------------------------------------------------
            n_floats = byte_length // 4
            if pos + byte_length > len(response):
                raise MySolensoException("Float array extends beyond response buffer.")

            floats = list(struct.unpack_from(f'<{n_floats}f', response, pos))

            # ----------------------------------------------------------
            # 5. Zip dates → values (protobuf padding zeros are ignored)
            # ----------------------------------------------------------
            self._result: Dict[str, float] = {
                date: round(value, 2)
                for date, value in zip(dates, floats)
            }

            _LOG.debug(
                "%s - parsed %d dates, %d floats → %d pairs.",
                self.__class__.__name__, len(dates), len(floats), len(self._result),
            )

        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                f"Failed to parse day-of-year response: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------

    def set_station_id(self, id: int, refresh: bool = True) -> None:
        """Switch the active station and optionally reload production data.

        The provided ``id`` is validated against the station list from
        :attr:`~mysolenso.services.station.MySolensoStation.stations`.

        Args:
            id (int): Station ID to activate. Must exist in the account's
                station list.
            refresh (bool): If ``True`` (default), immediately calls
                :meth:`_get_count_by_day_of_year` to reload data for the
                new station. Set to ``False`` to defer the network call.

        Raises:
            MySolensoException: If ``id`` is not found in the account's
                station list, or if the subsequent API call fails.

        Example:
            ::

                client.day_of_year.set_station_id(43)
                print(client.day_of_year.get_data["2026-01-01"])
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
            self._get_count_by_day_of_year()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def get_data(self) -> Dict[str, float]:
        """Daily energy production indexed by date.

        Example:
            {'2026-04-01': 4825.0, '2026-04-02': 10020.0, '2026-04-03': 11647.0, '2026-04-04': 16508.0, '2026-04-05': 13898.0, '2026-04-06': 25402.0, '2026-04-07': 25699.0, '2026-04-08': 25338.0, '2026-04-09': 21791.0, '2026-04-10': 22282.0, '2026-04-11': 6802.0, '2026-04-12': 16980.0, '2026-04-13': 20415.0, '2026-04-14': 26688.0, '2026-04-15': 18080.0, '2026-04-16': 23780.0, '2026-04-17': 24516.0, '2026-04-18': 17712.0, '2026-04-19': 23548.0, '2026-04-20': 22471.0, '2026-04-21': 24273.0, '2026-04-22': 26415.0, '2026-04-23': 28823.0, '2026-04-24': 28643.0, '2026-04-25': 27013.0, '2026-04-26': 26410.0, '2026-04-27': 22913.0, '2026-04-28': 23101.0, '2026-04-29': 25910.0, '2026-04-30': 29276.0, '2026-05-01': 23831.0, '2026-05-02': 25386.0, '2026-05-03': 13307.0, '2026-05-04': 10231.0, '2026-05-05': 7342.0, '2026-05-06': 16156.0, '2026-05-07': 21370.0, '2026-05-08': 28599.0, '2026-05-09': 29313.0, '2026-05-10': 11381.0, '2026-05-11': 14577.0, '2026-05-12': 25201.0, '2026-05-13': 14353.0, '2026-05-14': 17647.0, '2026-05-15': 0.0}
        
        Returns a dictionary where:

        - **Keys** are date strings in ``YYYY-MM-DD`` format.
        - **Values** are energy production in Wh (``float``), rounded to
          2 decimal places. Days with no production have a value of ``0.0``.

        Returns:
            Dict[str, float]: Complete date → Wh mapping for the active
            station, covering every day since commissioning up to today.

        Example:
            ::

                data = client.day_of_year.get_data
                # {"2025-06-01": 28612.5, "2025-06-02": 31072.0, ..., "2026-05-15": 0.0}

                # Today's production (may be 0 if not yet updated)
                from datetime import date
                today = str(date.today())
                print(data.get(today, "date not found"))
        """
        return self._result