#!/usr/bin/env python

import logging
import sys
import signal
import argparse
import asyncio

from typing import Any
from mysolenso import MySolenso
from mysolenso.exceptions import (
    MySolensoException,
    MySolensoAuthenticationException,
    MySolensoConnectionException,
)

_LOG = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

# Suppress verbose debug logs from the underlying HTTP library.
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Shared state dict used by the signal handler to request a clean shutdown.
VAR: dict[str, Any] = {}


async def main() -> None:
    """Entry point: parse CLI arguments, connect to Solenso, and display DTU data."""
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description="Demonstrate DTU and microinverter retrieval via MySolenso."
    )
    parser.add_argument(
        "--username",
        required=True,
        type=str,
        help="Solenso account e-mail address.",
    )
    parser.add_argument(
        "--password",
        required=False,
        default=None,
        help="Encrypted Solenso password (from pwdsolenso). Omit when using --token.",
    )
    parser.add_argument(
        "--token",
        required=False,
        default=None,
        help="Pre-obtained Solenso API token. Omit when using --password.",
    )
    args = parser.parse_args()

    username = args.username
    password = args.password
    token = args.token

    def _shutdown(*_: Any) -> None:
        """Signal handler: request a graceful shutdown on SIGINT (Ctrl-C)."""
        VAR["running"] = False  # type: ignore[assignment]

    signal.signal(signal.SIGINT, _shutdown)

    try:
        _LOG.info("Starting MySolenso...")

        # Initialise the main client. Authentication is performed automatically.
        client = MySolenso(
            username=username,
            password=password,
            token=token,
        )

        # --- DTU Select All -------------------------------------------------
        # Fetch the DTU record and the full list of attached microinverters.
        print("===================================")
        print("Station Data module")
        client.stationdatamodule.station_data_module_day_refresh()
        print("URL: ", client.stationdatamodule.full_url)

       
        
        print("===================================")
        print("Station Power by day")
        print("Day :", client.powerplaybackbyday.day)
        client.powerplaybackbyday.get_power_refresh()
        data = client.powerplaybackbyday.get_data
        date = data["date"]
        values = data["values"]
        for time, value in values.items():
            print(f"{date} {time} -> {value}")
            


        _LOG.info("MySolenso finished.")

    except MySolensoAuthenticationException as err:
        _LOG.error("Authentication error: %s", err)

    except MySolensoConnectionException as err:
        _LOG.error("Connection error: %s", err)

    except MySolensoException as err:
        _LOG.error("MySolenso error: %s", err)

    except Exception as err:
        _LOG.exception("Unexpected error: %s", err)


if __name__ == "__main__":
    asyncio.run(main())
