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


async def main_loop_password(username: str, password: str) -> None:
    """Run main loop."""
    _LOG.info("Start MySolensoAuth password...")

    try:
        client = MySolensoAuth(
            username=username,
            password=password,
        )

        print("===================================")
        print("Connected          :", client.isConnect())
        print("Token              :", client.token)
        print("Headers - hoymiles :", client.get_auth_headers_hoymiles())
        print("Headers - solenso  :", client.get_auth_headers_solenso())
        print("===================================")

    except MySolensoAuthenticationException as err:
        print("Authentication error:")
        print(err)

    except MySolensoConnectionException as err:
        print("Connection error:")
        print(err)

    except MySolensoException as err:
        print("MySolenso error:")
        print(err)

    except Exception as err:
        print("Unknown error:")
        print(err)
    finally:
        _LOG.info("End MySolensoAuth.")

async def main_loop_token(username: str, token: str) -> None:
    """Run main loop."""
    _LOG.info("Start MySolensoAuth password...")

    try:

        client = MySolensoAuth(
            username=username,
            token=token,
        )

        print("===================================")
        print("Connected          :", client.isConnect())
        print("Token              :", client.token)
        print("Headers - hoymiles :", client.get_auth_headers_hoymiles())
        print("Headers - solenso  :", client.get_auth_headers_solenso())
        print("===================================")

    except MySolensoAuthenticationException as err:
        print("Authentication error:")
        print(err)

    except MySolensoConnectionException as err:
        print("Connection error:")
        print(err)

    except MySolensoException as err:
        print("MySolenso error:")
        print(err)

    except Exception as err:
        print("Unknown error:")
        print(err)
    finally:
        _LOG.info("End MySolensoAuth.")

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

    if password is not None:
        await main_loop_password(username=username, password=password )
    elif token is not None:
        await main_loop_token(username=username, token=token )
    
    try:

        _LOG.info("Start MySolenso...")

        # Initialisation du client principal
        client = MySolenso(
            username=username,
            password=password,
            token=token,
        )

        print("===================================")
        print("Connected          :", client.auth.isConnect())
        print("Token              :", client.auth.token)
        print("Headers - hoymiles :", client.auth.get_auth_headers_hoymiles())
        print("Headers - solenso  :", client.auth.get_auth_headers_solenso())
        print("===================================")
        print("me - username :", client.me.username)
        print("me - name     :", client.me.name)
        print("===================================")
        print("station - id :", client.station.station_id)
        print("station - ak :", client.station.ak)
        print("===================================")
        print("stationdata - id                :", client.stationdata.station_id)
        print("stationdata - money_unit        :", client.stationdata.money_unit)
        print("stationdata - electricity_price :", client.stationdata.electricity_price)
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
