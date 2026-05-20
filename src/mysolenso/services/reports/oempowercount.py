"""MySolenso OEM PV energy totals (count) report service.

Provides the :class:`MySolensoOEMPowerCount` class, which queries the
``/oem_count`` Solenso endpoint and returns aggregated PV and consumption
energy totals for a given station over a configurable date range.

Unlike :class:`~mysolenso.services.reports.oempower.MySolensoOEMPower`,
which returns one record *per day*, this service returns a single
aggregated summary for the entire requested date range:

- ``total_pv_eq`` - total PV energy produced (kWh, as a string).
- ``total_consumption_eq`` - total consumption energy (kWh, or ``"0"``
  when no consumption meter is present).

By default the service queries **today** (or yesterday before 01:00).
Use :meth:`~MySolensoOEMPowerCount.set_day` to change the date range
and :meth:`~MySolensoOEMPowerCount.set_station` to switch the station.

This module is instantiated automatically by :class:`~mysolenso.MySolenso`
and is accessible via ``client.oem_power_count``.

Example:
    ::

        client = MySolenso(username="user", token="tok")

        client.oem_power_count.set_day("2026-04-01", "2026-04-30")
        print(client.oem_power_count.total_pv)          # e.g. "91.22"
        print(client.oem_power_count.total_consumption)  # e.g. "0"
        print(client.oem_power_count.all_data)           # raw dict
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from ...post import MySolensoPost
from ...const import API_OEM_COUNT
from ...exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoOEMPowerCount:
    """Aggregated OEM PV and consumption energy totals over a date range.

    Queries the ``/oem_count`` Solenso endpoint and exposes the total
    PV energy produced and total consumption energy for the active
    station over the configured date range.

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
        :meth:`_get_oem_power_count` explicitly to load the first dataset.

    Example:
        ::

            client = MySolenso(username="admin", token="tok")
            count = client.oem_power_count

            count.set_day("2026-04-01", "2026-04-30")
            print(count.total_pv)           # "415.72"
            print(count.total_consumption)  # "0"
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
        """Switch the active station and optionally reload power count data.

        The provided ``id`` is validated against the station list from
        :attr:`~mysolenso.services.station.MySolensoStation.stations`.

        Args:
            id (int): Station ID to activate. Must exist in the account's
                station list.
            refresh (bool): If ``True`` (default), immediately calls
                :meth:`_get_oem_power_count` to reload data for the new
                station. Set to ``False`` to defer the network call.

        Raises:
            MySolensoException: If ``id`` is not found in the account's
                station list, or if the subsequent API call fails.

        Example:
            ::

                client.oem_power_count.set_station(43)
                print(client.oem_power_count.total_pv)
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
            self._get_oem_power_count()

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
                :meth:`_get_oem_power_count` to reload data for the new
                range. Set to ``False`` to defer the network call.

        Raises:
            MySolensoException:
                - If either date string is not exactly 10 characters.
                - If either date is outside ``[1900-01-01, today]``.
                - If ``day_min > day_max``.
                - If either date string cannot be parsed as ``YYYY-MM-DD``.

        Example:
            ::

                client.oem_power_count.set_day("2026-01-01", "2026-03-31")
                print(client.oem_power_count.total_pv)
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
                self._get_oem_power_count()

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

    def _get_oem_power_count(self) -> None:
        """Query the ``/oem_count`` endpoint and store the aggregated totals.

        Sends a POST request to the Solenso OEM count endpoint with the
        current station ID and date range. The response is expected to be
        a JSON object containing:

        - ``total_pv_eq`` *(str)* - total PV energy in kWh for the period.
        - ``total_consumption_eq`` *(str)* - total consumption energy in kWh
          (``"0"`` when no consumption meter is installed).

        The raw response dict is stored in ``_all_data``. The two totals
        are also extracted as cleaned strings in ``_total_pv`` and
        ``_total_consumption`` (``None`` is converted to ``None``).

        Raises:
            MySolensoException:
                - If the API returns an empty or falsy response body.
                - If any network or JSON parsing error occurs.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())

            # Build the request body: station list, mode, and date range.
            # Note: no pagination - this endpoint returns a single aggregate.
            self._client.set_raw_payload({
                "WAITING_PROMISE": False,
                "body": {
                    "sid_list": [self._station_id],
                    "mode": 1,
                    "start_date": self._day_min,
                    "end_date": self._day_max,
                }
            })
            response = self._client.post(API_OEM_COUNT)

            # Guard against empty or null responses.
            if not response:
                msg = (
                    f"{self.__class__.__name__} - _get_oem_power_count: "
                    f"response data not found."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)

            # Store the complete raw response dictionary.
            self._all_data = response

            # Helper to convert None → None, everything else → stripped string.
            def _clean(value):
                return str(value).strip() if value is not None else None

            # Extract and clean the two aggregate fields.
            self._total_pv          = _clean(response.get("total_pv_eq"))
            self._total_consumption = _clean(response.get("total_consumption_eq"))

        except MySolensoException:
            raise
        except Exception as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def oem_power_refresh(self) -> None:
        """Re-fetch OEM power count data for the current station and range.

        Convenience method that delegates to :meth:`_get_oem_power_count`.
        Call this after the underlying data may have changed (e.g. for
        intra-day monitoring).

        Example:
            ::

                client.oem_power_count.oem_power_refresh()
                print(client.oem_power_count.total_pv)
        """
        self._get_oem_power_count()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        """Raw aggregated response dictionary from the API.

        Returns the complete JSON object as returned by ``/oem_count``,
        without any post-processing.

        Returns:
            dict: Aggregated energy totals for the active station and
            date range, typically containing:

            - ``"total_pv_eq"`` *(str)* - total PV energy in kWh.
            - ``"total_consumption_eq"`` *(str)* - total consumption in kWh.

        Example:
            ::

                client.oem_power_count.set_day("2026-04-01", "2026-04-30")
                print(client.oem_power_count.all_data)
                # {"total_pv_eq": "91.22", "total_consumption_eq": "0"}

        Data example::

            {
                "total_pv_eq": "91.22",
                "total_consumption_eq": "0"
            }
        """
        return self._all_data

    @property
    def total_pv(self) -> str:
        """Total PV energy produced over the queried date range (kWh).

        Returns:
            str: PV energy total as a string (e.g. ``"91.22"``), or
            ``None`` if the field was absent from the API response.

        Example:
            ::

                client.oem_power_count.set_day("2026-04-01", "2026-04-30")
                print(client.oem_power_count.total_pv)  # "91.22"
        """
        return self._total_pv

    @property
    def total_consumption(self) -> str:
        """Total consumption energy over the queried date range (kWh).

        Returns:
            str: Consumption energy total as a string (e.g. ``"0"``), or
            ``None`` if the field was absent from the API response.
            Returns ``"0"`` when no consumption meter is installed.

        Example:
            ::

                client.oem_power_count.set_day("2026-04-01", "2026-04-30")
                print(client.oem_power_count.total_consumption)  # "0"
        """
        return self._total_consumption
