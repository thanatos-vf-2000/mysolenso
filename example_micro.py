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

        client.dtuselectall.dtu_select_all_refresh()
        _dtu_list_micros =  client.dtuselectall.list_micros
        print("===================================")
        print("Micro Find")
        _micro_id = None
        for item in _dtu_list_micros[:10]:
            _micro_id=item["id"]
        print("ID:", _micro_id)
        client.microfind.set_micro(
            id=_micro_id, 
            refresh=True
        )
        _micro_info = client.microfind.all_data
        print("station_name: %20s" % (_micro_info.get("station_name")))
        
        
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
