"""Main entry point for the MySolenso library.

This module exposes the :class:`MySolenso` facade class, which groups all
library sub-modules into a single, unified interface. Most users only need
to import and instantiate this class.

Sub-modules initialised at construction
---------------------------------------
1. :class:`~mysolenso.auth.MySolensoAuth` — authentication and token management.
2. :class:`~mysolenso.services.me.MySolensoMe` — authenticated user profile.
3. :class:`~mysolenso.services.station.MySolensoStation` — PV station list and
   active station selection.
4. :class:`~mysolenso.services.stationdata.MySolensoStationData` — detailed
   configuration of the active station.
5. :class:`~mysolenso.services.stationcount.MySolensoStationCount` — real-time
   and cumulative energy counters.
6. :class:`~mysolenso.services.powerbyday.MySolensoPowerByDay` — intra-day
   grid power curve for today.
7. :class:`~mysolenso.services.dayofyeay.MySolensoCountByDayOfYeay` — full
   day-of-year production history (Wh per day since commissioning).
8. :class:`~mysolenso.services.reports.powerbystation.MySolensoPowerByStation`
   — per-station power data in 15-minute intervals for a single day.
9. :class:`~mysolenso.services.reports.oempower.MySolensoOEMPower` — OEM daily
   PV energy list report (one record per day, paginated).
10. :class:`~mysolenso.services.reports.oempowercount.MySolensoOEMPowerCount`
    — OEM aggregated PV and consumption totals over a date range.

Example
-------
Connect with an encrypted password::

    from mysolenso import MySolenso

    client = MySolenso(username="jdoe@example.com", password="encrypted_pass")

    # Authentication status
    print(client.auth.isConnect())          # True

    # User profile
    print(client.me.name)
    print(client.me.email)

    # Active station
    print(client.station.station_id)
    print(client.station.install_power)

    # Real-time energy counters
    print(client.stationcount.today_eq)     # kWh produced today
    print(client.stationcount.real_power)   # current output in W

    # Intra-day power curve (15-min intervals)
    curve = client.powerbyday.get_data
    print(curve["date"], curve["values"])   # {"08:00": 512.0, ...}

    # Historical daily production since commissioning
    history = client.countbydayofyear.get_data
    print(history["2026-01-01"])            # Wh produced on that day

    # OEM daily list report for a date range
    client.oempower.set_day("2026-04-01", "2026-04-30")
    for record in client.oempower.all_data:
        print(record["date"], record["pv_eq"], "kWh")

    # OEM aggregated totals for the same range
    client.oempowercount.set_day("2026-04-01", "2026-04-30")
    print(client.oempowercount.total_pv)    # e.g. "415.72"

Connect with an existing token (skips the authentication network call)::

    client = MySolenso(username="jdoe@example.com", token="eyJ...")
"""

from __future__ import annotations

import logging
from typing import Optional

from .auth import MySolensoAuth
from .services.me import MySolensoMe
from .services.station import MySolensoStation
from .services.stationdata import MySolensoStationData
from .services.stationcount import MySolensoStationCount
from .services.powerbyday import MySolensoPowerByDay
from .services.dayofyeay import MySolensoCountByDayOfYeay
from .services.reports.powerbystation import MySolensoPowerByStation
from .services.reports.oempower import MySolensoOEMPower
from .services.reports.oempowercount import MySolensoOEMPowerCount

_LOG = logging.getLogger(__name__)


class MySolenso:
    """Main facade for the MySolenso library.

    Instantiates and groups all service sub-modules under a single object.
    Authentication and initial data loading are performed automatically at
    construction time in the order listed in the module docstring.

    Args:
        username (str): Solenso account e-mail address or identifier.
        password (Optional[str]): Encrypted password. When provided, a POST
            request is made to the authentication endpoint to obtain a
            session token. Must be omitted when ``token`` is given.
        token (Optional[str]): Pre-obtained session token. When provided,
            the authentication network call is skipped entirely.

    Raises:
        MySolensoConnectionException: If ``username`` is empty, or if
            neither ``password`` nor ``token`` is supplied.
        MySolensoAuthenticationException: If the supplied credentials are
            rejected by the Solenso API.
        MySolensoException: On any network error or missing data during
            sub-module initialisation.

    Attributes:
        username (str): Account identifier supplied at construction.
        password (Optional[str]): Encrypted password kept in memory
            (used only during construction; not reused afterward).
        token (Optional[str]): Initial token supplied at construction.
        auth (MySolensoAuth): Session management and HTTP authorisation headers.
            Provides :meth:`~mysolenso.auth.MySolensoAuth.get_auth_headers_solenso`
            and :meth:`~mysolenso.auth.MySolensoAuth.get_auth_headers_hoymiles`.
        me (MySolensoMe): Authenticated user profile (name, email, role, group).
        station (MySolensoStation): PV station list and active station control.
            Use :meth:`~mysolenso.services.station.MySolensoStation.set_station`
            to switch the active station; all other services update accordingly.
        stationdata (MySolensoStationData): Detailed technical configuration of
            the active station: timezone, installed capacity, pricing, inverters.
        stationcount (MySolensoStationCount): Real-time and cumulative energy
            counters — today/month/year/lifetime yield, current power, CO₂ offset.
        powerbyday (MySolensoPowerByDay): Intra-day grid power curve. Returns a
            ``{HH:MM: watts}`` mapping for the active station and a given date.
            Use :meth:`~mysolenso.services.powerbyday.MySolensoPowerByDay.set_day`
            to query a specific date.
        countbydayofyear (MySolensoCountByDayOfYeay): Full production history as
            a ``{YYYY-MM-DD: Wh}`` dictionary covering every day since the station
            was commissioned.
        powerbystation (MySolensoPowerByStation): Per-station power data in
            15-minute intervals for a single day (PV, consumption, grid, BMS).
        oempower (MySolensoOEMPower): OEM daily PV energy list report. Returns one
            record per day with ``pv_eq`` (kWh) and auxiliary fields. Use
            :meth:`~mysolenso.services.reports.oempower.MySolensoOEMPower.set_day`
            to set the date range.
        oempowercount (MySolensoOEMPowerCount): OEM aggregated PV and consumption
            totals over a date range. Exposes :attr:`total_pv` and
            :attr:`total_consumption` for the configured period. Use
            :meth:`~mysolenso.services.reports.oempowercount.MySolensoOEMPowerCount.set_day`
            to set the date range.

    Example:
        ::

            from mysolenso import MySolenso
            from mysolenso.exceptions import MySolensoException

            try:
                client = MySolenso(username="jdoe",
                                   password="encrypted_pass")

                print(client.me.name)
                print(client.stationcount.today_eq)
                print(client.powerbyday.get_data["values"])

                # OEM report for the last month
                client.oempower.set_day("2026-04-01", "2026-04-30")
                print(client.oempower.power_data)

                client.oempowercount.set_day("2026-04-01", "2026-04-30")
                print(client.oempowercount.total_pv, "kWh total")

            except MySolensoException as e:
                print(f"Error: {e}")
    """

    def __init__(
        self,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        self.username = username
        self.password = password
        self.token    = token

        # 1. Authentication — must come first; all other services depend on it.
        self.auth = MySolensoAuth(
            username=self.username,
            password=self.password,
            token=self.token,
        )

        # 2. User profile — fetched immediately after authentication.
        self.me = MySolensoMe(self)

        # 3. Station list — determines which station is active.
        self.station = MySolensoStation(self)

        # 4. Station detail — technical configuration of the active station.
        self.stationdata = MySolensoStationData(self)

        # 5. Energy counters — real-time and cumulative production figures.
        self.stationcount = MySolensoStationCount(self)

        # 6. Intra-day power curve — today's grid power in 15-min intervals.
        self.powerbyday = MySolensoPowerByDay(self)

        # 7. Day-of-year history — daily Wh totals since commissioning.
        self.countbydayofyear = MySolensoCountByDayOfYeay(self)

        # 8. Per-station power report — 15-min power data for a single day.
        self.powerbystation = MySolensoPowerByStation(self)

        # 9. OEM daily list report — one JSON record per day (paginated).
        self.oempower = MySolensoOEMPower(self)

        # 10. OEM aggregated totals — single-call PV + consumption summary.
        self.oempowercount = MySolensoOEMPowerCount(self)