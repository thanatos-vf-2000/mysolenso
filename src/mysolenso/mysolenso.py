"""Main entry point for the MySolenso library.

This module exposes the :class:`MySolenso` facade class, which groups all
library sub-modules into a single, unified interface:

- :attr:`MySolenso.auth` — session management and token handling
- :attr:`MySolenso.me` — user account information
- :attr:`MySolenso.station` — PV station list and active station selection
- :attr:`MySolenso.stationdata` — detailed configuration of the active station
- :attr:`MySolenso.stationcount` — real-time and cumulative energy counters
- :attr:`MySolenso.powerbyday` — intra-day grid power curve
- :attr:`MySolenso.countbydayofyear` — day-of-year energy production history

This is the only class that most users need to import.

Example:
    Connect with an encrypted password::

        from mysolenso import MySolenso

        client = MySolenso(username="jdoe", password="encrypted_pass")

        # Authentication
        print(client.auth.isConnect())   # True

        # User profile
        print(client.me.name)
        print(client.me.email)

        # Active station
        print(client.station.station_id)
        print(client.station.install_power)

        # Energy counters
        print(client.stationcount.today_eq)
        print(client.stationcount.real_power)

        # Intra-day power curve
        curve = client.powerbyday.get_data
        print(curve["date"], curve["values"])

        # Historical daily production
        history = client.countbydayofyear.get_data
        print(history["2026-01-01"])  # Wh produced on that day

    Connect directly with an existing token (avoids the authentication
    network call)::

        client = MySolenso(username="jdoe", token="eyJ...")
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

    Instantiates and groups all sub-modules into a unified interface.
    Authentication and initial data loading are performed automatically
    at construction in the following order:

    1. :class:`~mysolenso.auth.MySolensoAuth` — authenticate and obtain token.
    2. :class:`~mysolenso.services.me.MySolensoMe` — fetch user profile.
    3. :class:`~mysolenso.services.station.MySolensoStation` — fetch station list.
    4. :class:`~mysolenso.services.stationdata.MySolensoStationData` — fetch station detail.
    5. :class:`~mysolenso.services.stationcount.MySolensoStationCount` — fetch energy counters.
    6. :class:`~mysolenso.services.powerbyday.MySolensoPowerByDay` — fetch today's power curve.
    7. :class:`~mysolenso.services.dayofyeay.MySolensoCountByDayOfYeay` — fetch production history.
    8. :class:`~mysolenso.services.powerbystation.MySolensoPowerByStation` — fetch power history.

    Args:
        username (str): Email address or Solenso account identifier.
        password (Optional[str]): Encrypted password. If provided, a network
            call is made to obtain the session token.
        token (Optional[str]): Existing session token. If provided, no
            additional authentication call is made.

    Raises:
        MySolensoConnectionException: If ``username`` is empty or if neither
            ``password`` nor ``token`` is provided.
        MySolensoAuthenticationException: If the credentials are invalid.
        MySolensoException: On network error or missing data during any
            sub-module initialisation.

    Attributes:
        username (str): Account identifier.
        password (Optional[str]): Password kept in memory (not reused after
            construction).
        token (Optional[str]): Initial token provided at construction.
        auth (MySolensoAuth): Session management and authorisation headers.
        me (MySolensoMe): User profile access.
        station (MySolensoStation): PV station list and active station
            selection.
        stationdata (MySolensoStationData): Detailed configuration of the
            active station (timezone, pricing, installed power, etc.).
        stationcount (MySolensoStationCount): Real-time and cumulative energy
            counters (today/month/year/total yield, current power, CO₂).
        powerbyday (MySolensoPowerByDay): Intra-day grid power curve
            (``{HH:MM: watts}`` for a given date).
        countbydayofyear (MySolensoCountByDayOfYeay): Full production history
            as a ``{YYYY-MM-DD: Wh}`` dictionary since commissioning.
        powerbystation (MySolensoPowerByStation): Full power history for one day

    Example:
        ::

            from mysolenso import MySolenso
            from mysolenso.exceptions import MySolensoException

            try:
                client = MySolenso(username="admin", password="encrypted_pass")
                print(client.me.name)
                print(client.stationcount.today_eq)
                print(client.powerbyday.get_data["values"])
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

        # 1. Authentication
        self.auth = MySolensoAuth(
            username=self.username,
            password=self.password,
            token=self.token,
        )

        # 2. User profile
        self.me = MySolensoMe(self)

        # 3. Station list
        self.station = MySolensoStation(self)

        # 4. Station detail
        self.stationdata = MySolensoStationData(self)

        # 5. Energy counters
        self.stationcount = MySolensoStationCount(self)

        # 6. Today's intra-day power curve
        self.powerbyday = MySolensoPowerByDay(self)

        # 7. Full day-of-year production history
        self.countbydayofyear = MySolensoCountByDayOfYeay(self)

        # 8. Full power history for one day
        self.powerbystation = MySolensoPowerByStation(self)
        
        self.oempower = MySolensoOEMPower(self)
        self.oempowercount = MySolensoOEMPowerCount(self)