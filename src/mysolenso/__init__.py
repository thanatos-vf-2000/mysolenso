"""mysolenso - Python library for the monitor.solenso.net API.

This library provides a simple, unified interface to the **Solenso**
photovoltaic monitoring platform. It handles authentication, user profile
retrieval, PV station data, real-time energy counters, historical production
data, and OEM reporting - all accessible from a single :class:`MySolenso`
client object.

Main modules
------------
- :mod:`mysolenso.mysolenso` - :class:`~mysolenso.MySolenso` facade (start here)
- :mod:`mysolenso.auth` - :class:`~mysolenso.auth.MySolensoAuth` authentication
- :mod:`mysolenso.services.me` - Authenticated user profile
- :mod:`mysolenso.services.station` - Photovoltaic station list and selection
- :mod:`mysolenso.services.stationdata` - Station detailed configuration
- :mod:`mysolenso.services.stationcount` - Real-time energy counters
- :mod:`mysolenso.services.powerbyday` - Intra-day grid power curve
- :mod:`mysolenso.services.dayofyeay` - Day-of-year production history (Wh per day)
- :mod:`mysolenso.services.reports.powerbystation` - Per-station daily power report
- :mod:`mysolenso.services.reports.oempower` - OEM daily PV energy list report
- :mod:`mysolenso.services.reports.oempowercount` - OEM aggregated PV/consumption totals
- :mod:`mysolenso.exceptions` - Exception hierarchy
- :mod:`mysolenso.const` - API endpoint URLs and network constants
- :mod:`mysolenso.post` - Internal HTTP POST client

Quick start
-----------
::

    from mysolenso import MySolenso

    client = MySolenso(username="user@example.com", password="encrypted_pass")

    # User profile
    print(client.me.name)

    # Real-time counters
    print(client.stationcount.today_eq)      # today's production in kWh
    print(client.stationcount.real_power)    # current power in W

    # Intra-day power curve
    data = client.powerbyday.get_data
    print(data["date"], data["values"])      # {"08:00": 512.0, ...}

    # Full production history since commissioning
    history = client.countbydayofyear.get_data
    print(history["2026-01-01"])             # e.g. 3241.5 Wh

    # OEM daily list report
    client.oempower.set_day("2026-04-01", "2026-04-30")
    for record in client.oempower.all_data:
        print(record["date"], record["pv_eq"], "kWh")

    # OEM aggregated totals
    client.oempowercount.set_day("2026-04-01", "2026-04-30")
    print(client.oempowercount.total_pv)     # e.g. "415.72"

Error handling
--------------
All library errors inherit from :exc:`MySolensoException`::

    from mysolenso import MySolenso, MySolensoException

    try:
        client = MySolenso(username="user", password="wrong")
    except MySolensoException as e:
        print(e)

Source: https://github.com/thanatos-vf-2000/mysolenso
"""

from .exceptions import (
    MySolensoException,
    MySolensoConnectionException,
    MySolensoAuthenticationException,
)
from .auth import MySolensoAuth
from .mysolenso import MySolenso

__all__ = [
    "MySolensoException",
    "MySolensoConnectionException",
    "MySolensoAuthenticationException",
    "MySolensoAuth",
    "MySolenso",
]
