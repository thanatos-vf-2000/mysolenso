"""MySolenso detailed PV station data service.

Provides the :class:`MySolensoStationData` class, which queries the
``/station_find`` endpoint and exposes extended configuration and runtime
data for a specific photovoltaic station.

Unlike :class:`~mysolenso.services.station.MySolensoStation`, which returns
a paginated list of stations, this service fetches the **full detail record**
of a single station (pricing, timezone, config, local time, etc.).

This module is intended to be instantiated by :class:`~mysolenso.MySolenso`
and accessed via ``client.station_data``.

Example:
    ::

        client = MySolenso(username="jdoe", token="tok")

        # Detailed data for the currently active station
        print(client.station_data.station_id)
        print(client.station_data.name)
        print(client.station_data.electricity_price)
        print(client.station_data.local_time)
        print(client.station_data.timezone)

        # Switch to a different station by its ID
        client.station_data.set_station_find(43)
        print(client.station_data.install_power)
"""

from __future__ import annotations

import logging
from typing import Union

from ..post import MySolensoPost
from ..const import API_STATION_FIND
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoStationData:
    """Detailed configuration and runtime data for a single PV station.

    Queries the ``/station_find`` endpoint with a station ID and exposes the
    full detail record as Python properties. The active station defaults to
    the one currently selected in the parent's
    :class:`~mysolenso.services.station.MySolensoStation` sub-module.

    Use :meth:`set_station_find` to switch to any station that belongs to
    the account (validated against the station list).

    Args:
        parent: Instance of :class:`~mysolenso.MySolenso` providing access
            to the ``auth`` and ``station`` sub-modules.

    Raises:
        MySolensoException: If ``parent.station.station_id`` is ``None``
            (no active station set), or if the API response is invalid.

    Attributes:
        parent: Reference to the parent :class:`~mysolenso.MySolenso` object.

    Note:
        Every call to :meth:`set_station_find` triggers a new network
        request to refresh all properties.

    Example:
        ::

            client = MySolenso(username="jdoe", token="tok")
            sd = client.station_data

            print(sd.station_id)          # active station ID
            print(sd.name)                # "My Solar Roof"
            print(sd.electricity_price)   # 0.1740
            print(sd.money_unit)          # "EUR"
            print(sd.local_time)          # "2026-05-14 10:32:00"
            sd.set_station_find(43)       # switch and reload
    """

    def __init__(self, parent) -> None:
        self.parent = parent

        # Guard: station_id must be resolved before instantiation
        if self.parent.station.station_id is None:
            _LOG.warning(
                "%s - MySolensoStationData station_id is None.",
                self.__class__.__name__,
            )
            raise MySolensoException("MySolensoStationData station_id is None.")

        self._station_find = self.parent.station.station_id

        # Initial data fetch for the active station
        self._get_station_find()

    # ------------------------------------------------------------------
    # Station selection
    # ------------------------------------------------------------------

    def set_station_find(self, id: int) -> None:
        """Switch the active station and reload all properties from the API.

        The provided ``id`` is validated against the station list returned by
        :attr:`~mysolenso.services.station.MySolensoStation.stations` to
        prevent requests for stations that do not belong to the account.

        Args:
            id (int): Station ID to activate. Must exist in the account's
                station list.

        Raises:
            MySolensoException: If ``id`` is not found in the account's
                station list, or if the subsequent API call fails.

        Example:
            ::

                client.station_data.set_station_find(999999)
                print(client.station_data.name)
        """
        stations = self.parent.station.stations
        exists = any(station.get("id") == id for station in stations)

        if not exists:
            msg = (
                f"{self.__class__.__name__} - set_station_find: "
                f"station {id} not found."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_find = id
        self._get_station_find()

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_station_find(self) -> None:
        """Query the API and refresh all station detail attributes.

        Sends a POST request to :data:`~mysolenso.const.API_STATION_FIND`
        with the current station ID, then maps every field of the response
        onto the instance's private attributes.

        Raises:
            MySolensoException: If the request fails, times out, or returns
                a malformed JSON response.
        """
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            self._client.set_raw_payload({
                "ERROR_BACK": True,
                "body": {"id": self._station_find},
                "WAITING_PROMISE": True,
            })
            response = self._client.post(API_STATION_FIND)

            self._all_data = response

            self._name              = self._get_data("name")
            self._create_at         = self._get_data("create_at")
            self._capacitor         = self._get_data("capacitor")
            self._address           = self._get_data("address")
            self._config            = self._get_data("config")
            self._is_stars          = self._get_data("is_stars")
            self._money_unit        = self._get_data("money_unit")
            self._electricity_price = self._get_data("electricity_price")
            self._timezone          = self._get_data("timezone")
            self._local_time        = self._get_data("local_time")
            self._install_power     = self._get_data("group")

        except Exception as e:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from e

    # ------------------------------------------------------------------
    # Internal data access
    # ------------------------------------------------------------------

    def _get_data(self, name: str) -> Union[int, float, str, dict, None]:
        """Return a field from the cached station detail response.

        Args:
            name (str): Field name to read from the raw response dict.

        Returns:
            Union[int, float, str, dict, None]: Field value, or ``None``
            if the key is absent.
        """
        return self._all_data.get(name, None)

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def all_data(self) -> dict:
        """Full raw response returned by the ``/station_find`` endpoint.

        Useful for accessing fields not exposed by the other properties.

        Example:
            {
                "id": 9999999,
                "gid": 123456,
                "name": "DOE JOHN",
                "type": 1,
                "tz_id": 42,
                "city_code": "FR13005000000000",
                "status": 40,
                "create_by": 293382,
                "create_at": "2025-11-08 10:44:51",
                "classify": 1,
                "tz_name": "UTC+01",
                "pic_path": "",
                "capacitor": "5",
                "address": "95 Moon Road, 99999 Galaxy, World",
                "layout_step": 2,
                "is_balance": 0,
                "is_reflux": 0,
                "remarks": "",
                "config": {
                    "sun_spec_num": 0,
                    "power_limit": "",
                    "power_limit_pf": "",
                    "power_limit_re": "",
                    "module_max_power": 0,
                    "owner_is_show_layout": 1,
                    "owner_is_modify_dev": 0,
                    "third_party_user": [],
                    "billing_type": 0,
                    "billing_start": "",
                    "billing_every": 0,
                    "client_type": 100,
                    "layout_show": 1,
                    "fcs": 0,
                    "ess_cfg_edit": 0,
                    "grid_type": 0,
                    "diy": 0,
                    "weather": 0,
                    "au": 0,
                    "cr": 0,
                    "split_power": 0,
                    "dw": 0,
                    "eps": 0
                },
                "is_stars": 0,
                "money_unit": "EUR",
                "electricity_price": 0.25,
                "in_price": 0,
                "usd": "",
                "nk_name": null,
                "int5m": 0,
                "is_3rd": 0,
                "dc": 0,
                "et": 0,
                "city_id": 41641,
                "weather_of_cid": 0,
                "timezone": {
                    "id": 42,
                    "dis_name": "(UTC+01:00) Windhoek",
                    "name": "Africa/Windhoek",
                    "tz_name": "UTC+01",
                    "offset": 7200000
                },
                "local_time": "2026-05-12 14:39:07",
                "parent_city": [
                    {
                        "id": 69,
                        "pid": 0,
                        "code": "FR00000000000000",
                        "weather_of_cid": 0,
                        "city_name": "World",
                        "country_code": "FR",
                        "level": 1
                    },
                    {
                        "id": 41636,
                        "pid": 69,
                        "code": "FR13000000000000",
                        "weather_of_cid": 0,
                        "city_name": "Galaxy",
                        "country_code": "FR",
                        "level": 2
                    },
                    {
                        "id": 41641,
                        "pid": 41636,
                        "code": "FR13005000000000",
                        "weather_of_cid": 0,
                        "city_name": "Moon",
                        "country_code": "FR",
                        "level": 3
                    }
                ],
                "latitude": "39.10884652257048",
                "longitude": "-76.77128918829347",
                "meter_location": 0,
                "owner_list": [
                    {
                        "uid": 111111,
                        "name": "John DOE",
                        "user_name": "JDOE"
                    }
                ],
                "group": {
                    "id": 123456,
                    "name": "Install Solenso",
                    "pid": 111139,
                    "type": 4,
                    "contact": "John Solenso",
                    "phone": "+33700000000",
                    "area": "",
                    "icon": ""
                },
                "money_data": {
                    "code": "EUR",
                    "unit": "€"
                },
                "warn_data": {
                    "s_uoff": false,
                    "s_ustable": false,
                    "s_uid": false,
                    "l3_warn": false,
                    "g_warn": false,
                    "me_warn": false,
                    "dl": null,
                    "pw_off": false
                },
                "bms_capacitor": "0",
                "inv_mode": 0,
                "create_by_name": "SOLENSO_ADMIN",
                "lack": 0,
                "ak": "aP7xQnLk9vTe41dR2mHyCuJ8zsKb",
                "flag_map": {
                    "gfi": 1
                }
            }
        Returns:
            dict: Complete dictionary from the ``data`` field of the response.
        """
        return self._all_data

    @property
    def station_id(self) -> int:
        """Identifier of the station currently loaded.

        Returns:
            int: Station ID used for the last ``/station_find`` API call.
        """
        return self._station_find

    @property
    def name(self) -> str:
        """Name of the photovoltaic installation.

        Returns:
            str: ``name`` field of the station detail record.
        """
        return self._name

    @property
    def create_at(self) -> str:
        """Date the station was registered on the platform.

        Returns:
            str: ``create_at`` field (ISO 8601 format or similar).
        """
        return self._create_at

    @property
    def capacitor(self) -> str:
        """Solar panel capacity of the station (kVA).

        Returns:
            str: ``capacitor`` field of the station detail record.
        """
        return self._capacitor

    @property
    def address(self) -> str:
        """Full geographic address of the station.

        Returns:
            str: ``address`` field of the station detail record.
        """
        return self._address

    @property
    def config(self) -> dict:
        """Station configuration object returned by the API.

        Contains hardware and software settings specific to the installation.

        Example:
            {
                "sun_spec_num": 0,
                "power_limit": "",
                "power_limit_pf": "",
                "power_limit_re": "",
                "module_max_power": 0,
                "owner_is_show_layout": 1,
                "owner_is_modify_dev": 0,
                "third_party_user": [],
                "billing_type": 0,
                "billing_start": "",
                "billing_every": 0,
                "client_type": 100,
                "layout_show": 1,
                "fcs": 0,
                "ess_cfg_edit": 0,
                "grid_type": 0,
                "diy": 0,
                "weather": 0,
                "au": 0,
                "cr": 0,
                "split_power": 0,
                "dw": 0,
                "eps": 0
            }
        Returns:
            dict: ``config`` field of the station detail record.
        """
        return self._config

    @property
    def is_stars(self) -> int:
        """Indicates whether the station is marked as a favourite ("starred").

        Returns:
            int: ``is_stars`` field.
        """
        return self._is_stars  # fix: was returning self.is_stars (infinite recursion)

    @property
    def money_unit(self) -> str:
        """Currency code used for financial calculations on this station.

        Returns:
            str: ``money_unit`` field (e.g. ``"EUR"``, ``"USD"``).
        """
        return self._money_unit

    @property
    def electricity_price(self) -> float:
        """Electricity sale/buy price configured for this station.

        Used by the platform to estimate revenue or savings from solar
        production.

        Returns:
            float: ``electricity_price`` field (unit depends on
            :attr:`money_unit`).
        """
        return self._electricity_price

    @property
    def timezone(self) -> dict:
        """Timezone information object for the station's location.

        Example:
            {
                "id": 42,
                "dis_name": "(UTC+01:00) Windhoek",
                "name": "Africa/Windhoek",
                "tz_name": "UTC+01",
                "offset": 7200000
            }
            
        Returns:
            dict: ``timezone`` field, typically containing an IANA timezone
            identifier and UTC offset.
        """
        return self._timezone

    @property
    def local_time(self) -> str:
        """Current local time at the station's location.

        Returns:
            str: ``local_time`` field as returned by the API
            (format: ``"YYYY-MM-DD HH:MM:SS"`` or similar).
        """
        return self._local_time

    @property
    def install_power(self) -> str:
        """Installed peak power of the station (in Wp or kWp).

        Returns:
            str: ``install_power`` field of the station detail record.
        """
        return self._install_power
