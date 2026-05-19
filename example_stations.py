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

        client.stationinfodevice.station_info_device_refresh()
        _sdi_dtu_list =  client.stationinfodevice.list_dtu
        _sdi_dtu_info =  client.stationinfodevice.list_dtu_info
        
        print("===================================")
        print("Station Info Device")
        print("SN Master          :", client.stationinfodevice.sn)

        #Display 10 values
        print("DTU list:")
        for item in _sdi_dtu_list[:10]:
            print("SN: %15s" % (item["sn"]))
        
        #Display 10 values
        print("DTU info:")
        for item in _sdi_dtu_info[:10]:
            print("SN: %15s - DTU %11s - MODEL %15s" % (item["sn"], item["dtu_sn"], item["model_no"]))
        
        client.stationcountdevice.station_count_device_refresh()
        print("Station Count Device")
        print("station_num:", client.stationcountdevice.station_num)
        
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
