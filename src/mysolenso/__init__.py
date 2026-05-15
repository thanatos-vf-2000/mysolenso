"""mysolenso — Python library for the monitor.solenso.net API.

This library provides a simple interface to the **Solenso** photovoltaic
monitoring platform from Python. It handles authentication, user profile
retrieval, PV station data, energy counters, and historical production data.

Main modules:

- :mod:`mysolenso.mysolenso` — :class:`~mysolenso.MySolenso` facade (start here)
- :mod:`mysolenso.auth` — :class:`~mysolenso.auth.MySolensoAuth` authentication
- :mod:`mysolenso.services.me` — User profile
- :mod:`mysolenso.services.station` — Photovoltaic station list
- :mod:`mysolenso.services.stationdata` — Station detailed configuration
- :mod:`mysolenso.services.stationcount` — Real-time energy counters
- :mod:`mysolenso.services.powerbyday` — Intra-day power curve
- :mod:`mysolenso.services.dayofyeay` — Day-of-year production history
- :mod:`mysolenso.exceptions` — Exception hierarchy
- :mod:`mysolenso.const` — Constants (URLs, timeout)
- :mod:`mysolenso.post` — Internal HTTP client

Minimal usage::

    from mysolenso import MySolenso

    client = MySolenso(username="user@example.com", password="encrypted_pass")
    print(client.me.name)
    print(client.stationcount.today_eq)
    print(client.powerbyday.get_data)
    print(client.countbydayofyear.get_data["2026-01-01"])

Error handling::

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
