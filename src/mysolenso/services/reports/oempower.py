"""MySolenso OEM PV energy report service.

Provides the :class:`MySolensoOEMPower` class, which queries the
``/oem_eq`` Solenso endpoint and returns a list of daily PV energy
production records for a given station over a configurable date range.

The API returns a JSON payload with a ``list`` of daily records and a
``total`` count. Each record contains the station ID, owner name,
timezone, date, PV energy in kWh (``pv_eq``), and several other
consumption/grid fields.

By default the service queries **today** (or yesterday before 01:00)
for a single day. Use :meth:`~MySolensoOEMPower.set_day` to adjust
the date range and :meth:`~MySolensoOEMPower.set_station` to switch
the active station.

This module is instantiated automatically by :class:`~mysolenso.MySolenso`
and is accessible via ``client.oem_power``.

Example:
    ::

        client = MySolenso(username="user", token="tok")

        # Fetch data for a custom date range
        client.oem_power.set_day("2026-04-01", "2026-04-30")
        records = client.oem_power.all_data
        for r in records:
            print(r["date"], r["pv_eq"], "kWh")

        # Simplified view: date + power only
        print(client.oem_power.power_data)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from ...post import MySolensoPost
from ...const import API_OEM_EQ
from ...exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoOEMPower:
    """OEM daily PV energy report for a single station over a date range.

    Queries the ``/oem_eq`` Solenso endpoint and exposes the raw JSON
    record list as well as a simplified ``{date, power}`` view.

    The date range defaults to **today** (or yesterday before 01:00 to
    avoid empty datasets at midnight). Call :meth:`set_day` to change it
    and :meth:`set_station` to switch the monitored station.

    Args:
        parent: Instance of :class:`~mysolenso.MySolenso` providing access
            to the ``auth`` and ``station`` sub-modules.

    Raises:
        MySolensoException: If ``parent.station.station_id`` is ``None``.

    Attributes:
        parent: Reference to the parent :class:`~mysolenso.MySolenso` object.

    Note:
        Data is **not** fetched automatically at construction time.
        Call :meth:`set_day` (with ``refresh=True``, the default) or
        :meth:`_get_oem_pv` explicitly to load the first dataset.

    Example:
        ::

            client = MySolenso(username="admin", token="tok")
            oem = client.oem_power

            oem.set_day("2026-04-01", "2026-04-30")
            print(oem.all_data)     # full JSON list
            print(oem.power_data)   # [{date, power}, ...]
    """

    def __init__(self, parent) -> None:
        self.parent = parent

        # Validate that a station has already been selected by the parent.
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = self.parent.station.station_id

        # Default to today; fall back to yesterday before 01:00 to avoid
        # returning an empty dataset at midnight before the first inverter
        # measurement of the day arrives.
        now = datetime.now()
        if now.hour < 1:
            self._day_min = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            self._day_min = now.strftime("%Y-%m-%d")

        # By default the range covers a single day (min == max).
        self._day_max = self._day_min

    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------

    def set_station(self, id: int, refresh: bool = True) -> None:
        """Switch the active station and optionally reload power data.

        The provided ``id`` is validated against the station list from
        :attr:`~mysolenso.services.station.MySolensoStation.stations`.

        Args:
            id (int): Station ID to activate. Must exist in the account's
                station list.
            refresh (bool): If ``True`` (default), immediately calls
                :meth:`_get_oem_pv` to reload data for the new station.
                Set to ``False`` to defer the network call.

        Raises:
            MySolensoException: If ``id`` is not found in the account's
                station list, or if the subsequent API call fails.

        Example:
            ::

                client.oem_power.set_station(43)
                print(client.oem_power.all_data)
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
            self._get_oem_pv()

    # ------------------------------------------------------------------
    # Date range selection
    # ------------------------------------------------------------------

    def set_day(self, day_min: str, day_max: str, refresh: bool = True) -> None:
        """Set the query date range and optionally reload the data.

        Both ``day_min`` and ``day_max`` must be valid ``YYYY-MM-DD``
        strings within ``[1900-01-01, today]``, and ``day_min`` must not
        be later than ``day_max``.

        Args:
            day_min (str): Start of the date range (inclusive), in
                ``YYYY-MM-DD`` format.
            day_max (str): End of the date range (inclusive), in
                ``YYYY-MM-DD`` format.
            refresh (bool): If ``True`` (default), immediately calls
                :meth:`_get_oem_pv` to reload data for the new range.
                Set to ``False`` to defer the network call.

        Raises:
            MySolensoException:
                - If either date string is not exactly 10 characters.
                - If either date is outside ``[1900-01-01, today]``.
                - If ``day_min > day_max``.
                - If either date string cannot be parsed as ``YYYY-MM-DD``.

        Example:
            ::

                client.oem_power.set_day("2026-04-01", "2026-04-30")
                print(client.oem_power.all_data)
        """
        try:
            # Basic length check before attempting strptime.
            if len(day_min) != 10:
                raise ValueError("Invalid length for day_min.")

            if len(day_max) != 10:
                raise ValueError("Invalid length for day_max.")

            # Compute the allowed date range.
            min_date = datetime(1900, 1, 1).date()
            max_date = datetime.now().date()

            # Parse both date strings.
            day_min_obj = datetime.strptime(day_min, "%Y-%m-%d").date()
            day_max_obj = datetime.strptime(day_max, "%Y-%m-%d").date()

            # Validate day_min is within the allowed range.
            if not (min_date <= day_min_obj <= max_date):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"day_min outside the allowed range "
                    f"{min_date} <= {day_min} <= {max_date}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            # Validate day_max is within the allowed range.
            if not (min_date <= day_max_obj <= max_date):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"day_max outside the allowed range "
                    f"{min_date} <= {day_max} <= {max_date}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            # Validate the range ordering: start must not be after end.
            if not (day_min_obj <= day_max_obj):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"date day_min not less or equal to day_max."
                    f"{day_min} <= {day_max}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            # Commit the new date range.
            self._day_min = day_min
            self._day_max = day_max

            # Reload data unless the caller deferred it.
            if refresh:
                self._get_oem_pv()

        except MySolensoException:
            raise
        except ValueError:
            msg = (
                f"{self.__class__.__name__} - set_day: "
                f"'{day_min}' or {day_max} are not a valid YYYY-MM-DD date."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_oem_pv(self) -> None:
        """Query the ``/oem_eq`` endpoint and store the JSON response.

        Sends a POST request to the Solenso OEM energy-equivalence
        endpoint with the current station ID and date range. The
        response is expected to be a JSON object with:

        - ``list``  *(list[dict])* - one record per day, each containing
          ``sid``, ``name``, ``date``, ``pv_eq``, ``consumption_eq``, etc.
        - ``total`` *(int)* - total number of records matching the query.

        Raises:
            MySolensoException:
                - If the API returns an empty or falsy response body.
                - If ``total`` is 0 (no data for the requested period).
                - If any network or JSON parsing error occurs.

        Note:
            The ``page_size`` is fixed at 10 in this implementation.
            For large date ranges, only the first 10 records are returned.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())

            # Build the request body: station list, mode, date range, pagination.
            self._client.set_raw_payload({
                "WAITING_PROMISE": False,
                "body": {
                    "sid_list": [self._station_id],
                    "mode": 1,
                    "start_date": self._day_min,
                    "end_date": self._day_max,
                    "page": 1,
                    "page_size": 10
                }
            })
            response = self._client.post(API_OEM_EQ)

            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_oem_pv: "
                    f"response data not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            # Store the full record list and the record count.
            self._all_data = response.get("list", {})
            self._total    = int(response.get("total", 0))

        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

        # Raise an explicit error when the API returned an empty dataset.
        if self._total == 0:
            _LOG.warning("%s - _get_oem_pv no data.", self.__class__.__name__)
            raise MySolensoException("_get_oem_pv no data.")

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def oem_pv_refresh(self) -> None:
        """Re-fetch OEM PV data for the current station and date range.

        Convenience method that delegates to :meth:`_get_oem_pv`.
        Call this after the underlying data may have changed (e.g. for
        intra-day monitoring).

        Example:
            ::

                client.oem_power.oem_pv_refresh()
                print(client.oem_power.all_data)
        """
        self._get_oem_pv()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> list:
        """Raw list of daily OEM PV records from the API.

        Each element is a dictionary with the following keys:

        - ``sid`` *(int)* - station identifier.
        - ``name`` *(str)* - station owner's display name.
        - ``tz_name`` *(str)* - IANA timezone name of the station.
        - ``date`` *(str)* - record date in ``YYYY-MM-DD`` format.
        - ``pv_eq`` *(str)* - daily PV energy production in kWh.
        - ``consumption_eq`` *(str)* - daily consumption energy in kWh,
          or ``"-"`` when no consumption meter is installed.
        - ``meter_c_eq`` *(str)* - meter energy value.
        - ``meter_location`` *(int)* - meter location type.
        - ``capacitor`` *(int)* - capacitor presence flag.
        - ``create_at`` *(str | None)* - record creation timestamp.
        - ``p2g`` *(Any | None)* - peer-to-grid value (may be ``null``).
        - ``lfg`` *(Any | None)* - load-following generation (may be ``null``).
        - ``eq_hour`` *(int)* - equivalent production hours.

        Returns:
            list[dict]: Complete raw record list for the active station
            and date range.

        Example:
            ::

                client.oem_power.set_day("2026-04-11", "2026-04-13")
                for record in client.oem_power.all_data:
                    print(record["date"], record["pv_eq"], "kWh")
                # 2026-04-11  14.58 kWh
                # 2026-04-12  25.2  kWh
                # 2026-04-13  14.35 kWh
        """
        return self._all_data

    @property
    def power_data(self) -> list[dict]:
        """Simplified list of ``{date, power}`` records.

        Extracts only the ``date`` and ``pv_eq`` fields from each raw
        record in :attr:`all_data`, returning a concise list suitable
        for charting or CSV export.

        Returns:
            list[dict]: Each element has exactly two keys:

            - ``"date"`` *(str)* - date in ``YYYY-MM-DD`` format.
            - ``"power"`` *(str)* - PV energy in kWh as a string
              (preserves the original API string representation).

        Raises:
            ValueError: If :attr:`all_data` is empty or missing.

        Example:
            ::

                client.oem_power.set_day("2026-04-01", "2026-04-03")
                for entry in client.oem_power.power_data:
                    print(entry["date"], entry["power"])
                # 2026-04-01  12.3
                # 2026-04-02  18.7
                # 2026-04-03  9.1
        """
        data_list = self._all_data

        # Guard against an uninitialised or empty data store.
        if not data_list:
            raise ValueError("all_data is missing or empty")

        # Return a minimal projection: date + pv_eq only.
        return [
            {
                "date": item["date"],
                "power": item["pv_eq"]
            }
            for item in data_list
        ]
