#!/usr/bin/env python
"""Station device information example for the MySolenso library.

This script demonstrates how to retrieve the device tree, device counts,
and geographic data for a Solenso PV station using the MySolenso client.

Usage
-----
.. code-block:: bash

    PYTHONPATH=./src/ python3 example_stations.py --username <USER> \\
        --password <PASSWORD_CRYPT>

    # or with a pre-obtained token
    PYTHONPATH=./src/ python3 example_stations.py --username <USER> \\
        --token <TOKEN>

Services demonstrated
---------------------
- ``client.stationinfodevice``  — Full device tree (DTU + microinverters)
  with serial numbers, firmware, and connection status.
- ``client.stationcountdevice`` — Device count summary by type.
- ``client.stationak``          — Station geographic coordinates and address.
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
    """Entry point: parse CLI arguments, connect to Solenso, and display station device data."""
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description="Demonstrate station device information retrieval via MySolenso."
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

        # --- Station Info Device --------------------------------------------
        # Fetch the full device tree: the primary DTU and all microinverters.
        client.stationinfodevice.station_info_device_refresh()
        _sdi_dtu_list = client.stationinfodevice.list_dtu
        _sdi_dtu_info = client.stationinfodevice.list_dtu_info

        print("===================================")
        print("Station Info Device")
        # The master SN is the DTU serial number for the active station.
        print("SN Master          :", client.stationinfodevice.sn)

        # Display serial numbers for up to 10 attached devices (microinverters).
        print("DTU list:")
        for item in _sdi_dtu_list[:10]:
            print("SN: %15s" % (item["sn"]))

        # Display extended info: SN, parent DTU SN, and hardware model number.
        print("DTU info:")
        for item in _sdi_dtu_info[:10]:
            print(
                "SN: %15s - DTU %11s - MODEL %15s"
                % (item["sn"], item["dtu_sn"], item["model_no"])
            )

        # --- Station Count Device -------------------------------------------
        # Retrieve device count summary (DTUs, microinverters, meters, etc.).
        client.stationcountdevice.station_count_device_refresh()
        print("Station Count Device")
        print("station_num:", client.stationcountdevice.station_num)

        # --- Station AK (geographic info) -----------------------------------
        # Retrieve station longitude, latitude, and human-readable address.
        print("===================================")
        print("Station AK:")
        client.stationak.station_ak_refresh()
        print("address:", client.stationak.address)

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
