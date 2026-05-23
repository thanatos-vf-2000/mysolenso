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
        print("Power by Station")
        print("name          :", _all_data.get("name"))
        
        #Display 10 values
        for item in _power_data[:10]:
            print("%-10s: %6i" % (item["date"], item["power"]))
            
        client.oempower.set_day(
            day_min="2026-04-11",
            day_max="2026-04-15",
            refresh=True)
        _oem_power = client.oempower.power_data
        print("===================================")
        print("OEM Power")
        for item in _oem_power:
            print("%-15s: %10s KwH" % (item["date"], item["power"]))
        
        client.oempowercount.set_day(
            day_min="2026-04-11",
            day_max="2026-04-15",
            refresh=True)
        print("===================================")
        print("OEM Power Count")
        print("Total pv         : %10s KwH" % client.oempowercount.total_pv)
        print("Total consumption: %10s KwH" % client.oempowercount.total_consumption)
        
        
        
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
