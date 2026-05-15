#!/usr/bin/env python

"""Basic usage example and testing of MySolenso."""

import logging
import sys
import signal
import argparse
import asyncio

from typing import Any
from mysolenso import MySolenso
from mysolenso.auth import MySolensoAuth
from mysolenso.exceptions import (
    MySolensoException,
    MySolensoAuthenticationException,
    MySolensoConnectionException,
)

_LOG = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

# Désactive les logs DEBUG urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

VAR: dict[str, Any] = {}


async def main() -> None:
    """Run example."""
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Test the MySolenso library.")
    parser.add_argument(
        "--username",
        required=True,
        type=str,
        help="Username",
    )
    parser.add_argument(
        "--password",
        required=False,
        default=None, 
        help="Password Crypted")
    parser.add_argument(
        "--token",
        required=False,
        default=None, 
        help="Token")
    args = parser.parse_args()

    username = args.username
    password = args.password
    token = args.token
    
    def _shutdown(*_: Any) -> None:
        VAR["running"] = False  # type: ignore[assignment]

    signal.signal(signal.SIGINT, _shutdown)
  
    try:

        _LOG.info("Start MySolenso...")

        # Initialisation du client principal
        client = MySolenso(
            username=username,
            password=password,
            token=token,
        )

        client.powerbystation.get_power_station_refresh()
        _all_data = client.powerbystation.all_data
        _power_data = client.powerbystation.extract_power_data
        
        print("===================================")
        print("name          :", _all_data.get("name"))
        
        for item in _power_data:
            print("%10s: %i" % (item["date"], item["power"]))
        
        
        _LOG.info("End MySolenso.")

    except MySolensoAuthenticationException as err:
        _LOG.error("Authentication error: %s", err)

    except MySolensoConnectionException as err:
        _LOG.error("Connection error: %s", err)

    except MySolensoException as err:
        _LOG.error("MySolenso error: %s", err)

    except Exception as err:
        _LOG.exception("Unknown error: %s", err)



if __name__ == "__main__":
    asyncio.run(main())
