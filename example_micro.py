#!/usr/bin/env python
"""Microinverter usage example for the MySolenso library.

This script demonstrates how to retrieve individual microinverter details
from the Solenso platform using the MySolenso client.

The example first fetches the DTU device list to obtain a valid microinverter
ID, then queries the full detail record for that microinverter.

Usage
-----
.. code-block:: bash

    PYTHONPATH=./src/ python3 example_micro.py --username <USER> \\
        --password <PASSWORD_CRYPT>

    # or with a pre-obtained token
    PYTHONPATH=./src/ python3 example_micro.py --username <USER> \\
        --token <TOKEN>

Services demonstrated
---------------------
- ``client.dtuselectall`` — Retrieve the list of microinverter IDs from the DTU.
- ``client.microfind``    — Fetch the full detail record for a single microinverter.
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
    """Entry point: parse CLI arguments, connect to Solenso, and display microinverter data."""
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description="Demonstrate microinverter detail retrieval via MySolenso."
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

        # --- Retrieve microinverter IDs from the DTU ------------------------
        # Fetch the DTU device list to find the available microinverter IDs.
        client.dtuselectall.dtu_select_all_refresh()
        _dtu_list_micros = client.dtuselectall.list_micros

        # --- Micro Find -----------------------------------------------------
        print("===================================")
        print("Micro Find")

        # Select the last microinverter ID from the list (up to 10 inspected).
        _micro_id = None
        for item in _dtu_list_micros[:10]:
            _micro_id = item["id"]
        print("ID:", _micro_id)

        # Fetch the full detail record for the selected microinverter.
        client.microfind.set_micro(
            id=_micro_id,
            refresh=True,
        )
        _micro_info = client.microfind.all_data
        print("station_name: %20s" % (_micro_info.get("station_name")))

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