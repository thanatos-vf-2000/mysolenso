#!/usr/bin/env python
"""DTU usage example for the MySolenso library.

This script demonstrates how to retrieve DTU (Data Transfer Unit) information
and associated microinverter data from the Solenso platform using the
MySolenso client.

Usage
-----
.. code-block:: bash

    PYTHONPATH=./src/ python3 example_dtu.py --username <USER> \\
        --password <PASSWORD_CRYPT>

    # or with a pre-obtained token
    PYTHONPATH=./src/ python3 example_dtu.py --username <USER> \\
        --token <TOKEN>

Services demonstrated
---------------------
- ``client.dtuselectall``     — DTU serial number and list of attached microinverters.
- ``client.stationcountdevice`` — Total device counts for the active station.
- ``client.dtufind``          — Full detail record for a specific DTU.
"""

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
        client.dtuselectall.dtu_select_all_refresh()
        _dtu_list_micros = client.dtuselectall.list_micros_info

        print("===================================")
        print("DTU Select All")
        print("SN Master          :", client.dtuselectall.dtu_sn)

        # Display up to 10 microinverters (sn, firmware version code, internal id).
        print("Micros list:")
        for item in _dtu_list_micros[:10]:
            print("SN: %15s - vc: %5s - ID: %10i" % (item["sn"], item["vc"], item["id"]))

        # --- Station Count Device -------------------------------------------
        # Retrieve device count summary for the active station.
        client.stationcountdevice.station_count_device_refresh()
        print("Station Count Device")
        print("station_num:", client.stationcountdevice.station_num)

        # --- DTU Find -------------------------------------------------------
        # Fetch the full detail record for the primary DTU.
        print("===================================")
        print("DTU find")
        _dtu_id = client.dtuselectall.dtu_id
        client.dtufind.set_dtu(
            id=_dtu_id,
            refresh=True,
        )
        _dtu_info = client.dtufind.all_data
        print("station_name: %20s" % (_dtu_info.get("station_name")))

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
