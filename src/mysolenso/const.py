"""Configuration constants for the MySolenso library.
 
This module centralises all fixed values used by the library: base URLs,
API endpoint paths, and network parameters. Modifying this file is sufficient
to retarget the library at a different environment (e.g. staging).
 
Two base URLs are used:
 
- :data:`BASE_URL_SOLENSO` - the Solenso monitoring platform (authentication,
  user profile, station list, station detail, energy counters, and OEM reports).
- :data:`BASE_URL_HOYMILES` - the Hoymiles inverter data API (intra-day
  power curve and day-of-year production totals).
 
Attributes
----------
DEFAULT_TIMEOUT (int)          : Network timeout in seconds for every HTTP
    request. Defaults to ``10``.
BASE_URL_SOLENSO (str)         : Root URL of the Solenso monitoring platform.
BASE_URL_HOYMILES (str)        : Root URL of the Hoymiles inverter data API.
API_AUTH_LOGIN (str)           : Solenso credential-based authentication endpoint.
API_USER_ME (str)              : Solenso authenticated user profile endpoint.
API_STATION_ME (str)           : Solenso paginated station list endpoint.
API_STATION_FIND (str)         : Solenso single-station detail endpoint.
API_STATION_COUNT (str)        : Solenso real-time energy counters endpoint.
API_STATION_AK (str)           : Solenso station geographic/address info endpoint.
API_STATION_INFO_DEVICE (str)  : Solenso station device tree endpoint.
API_STATION_COUNT_DEVICE (str) : Solenso station device count summary endpoint.
API_POWER_BY_STATION (str)     : Solenso per-station power data in 15-min intervals.
API_OEM_EQ (str)               : Solenso OEM daily PV energy list endpoint.
API_OEM_COUNT (str)            : Solenso OEM aggregated PV/consumption totals endpoint.
API_DTU_SELECT_ALL (str)       : Solenso DTU + microinverter list endpoint.
API_DTU_FIND (str)             : Solenso single-DTU detail endpoint.
API_MICRO_FIND (str)           : Solenso single-microinverter detail endpoint.
API_POWER_BY_DAY (str)         : Hoymiles intra-day grid power curve endpoint.
API_POWER_DAY_OF_YEAR (str)    : Hoymiles day-of-year production totals endpoint.
 
Example
-------
Direct use of constants (internal usage)::
 
    from mysolenso.const import API_AUTH_LOGIN, DEFAULT_TIMEOUT
 
    response = session.post(API_AUTH_LOGIN, json=payload, timeout=DEFAULT_TIMEOUT)
"""
 
DEFAULT_TIMEOUT: int = 10
"""Network timeout in seconds applied to every HTTP request (default: ``10``)."""
 
BASE_URL_SOLENSO: str = "https://monitor.solenso.net/platform/"
"""Root URL of the Solenso monitoring platform.
 
All Solenso endpoints (authentication, user profile, station management,
energy counters, and OEM reports) are built from this base URL.
"""
 
BASE_URL_HOYMILES: str = "https://neapi.hoymiles.com/pvm-data/api/"
"""Root URL of the Hoymiles inverter data API.
 
Used for endpoints that return binary protobuf responses: the intra-day
power curve and the day-of-year production history.
"""
 
# ---------------------------------------------------------------------------
# Authentication endpoints
# ---------------------------------------------------------------------------
 
API_AUTH_LOGIN: str = BASE_URL_SOLENSO + "api/gateway/iam/auth_login"
"""POST endpoint for credential-based authentication.
 
Request body: ``{"user_name": "<email>", "password": "<encrypted_pass>"}``.
Returns a JSON object containing the session token on success, or an error
message on failure.
"""
 
# ---------------------------------------------------------------------------
# User endpoints
# ---------------------------------------------------------------------------
 
API_USER_ME: str = BASE_URL_SOLENSO + "api/gateway/iam/fun_api_1_user_me"
"""POST endpoint for the connected user's account information.
 
Returns name, email, role, and group details for the authenticated user.
Requires a valid Solenso authorisation header.
"""
 
# ---------------------------------------------------------------------------
# Station endpoints (Solenso)
# ---------------------------------------------------------------------------
 
API_STATION_ME: str = BASE_URL_SOLENSO + "api/gateway/pvm/station_select_by_page"
"""POST endpoint for paginated retrieval of the user's PV stations.
 
Request body: ``{"page": 1, "page_size": <n>}``.
Returns ``{"total": <int>, "list": [<station_dict>, ...]}``.
"""
 
API_STATION_FIND: str = BASE_URL_SOLENSO + "api/gateway/pvm/station_find"
"""POST endpoint to retrieve the full detail record of a single PV station.
 
Request body: ``{"id": <station_id>}``.
Returns a single station dict with technical configuration, timezone, pricing,
installed capacity, and inverter details.
"""
 
API_STATION_COUNT: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm-data/data_count_station_real_data"
)
"""POST endpoint for real-time and cumulative energy counters of a station.
 
Returns today's yield, monthly/yearly/lifetime totals, current power output,
CO₂ savings, equivalent trees planted, and the last data timestamp.
"""
 
API_STATION_AK: str = BASE_URL_SOLENSO + "api/gateway/pvm-ext/station_ak_find"
"""POST endpoint to retrieve geographic and address information for a station.
 
Request body::
 
    {
        "ERROR_BACK": true,
        "body": {"sid": <station_id>, "ak": "<station_ak>"},
        "WAITING_PROMISE": true
    }
 
Returns the station's longitude, latitude, and human-readable address.
 
Used by :class:`~mysolenso.services.stations.ak.MySolensoStationAK`.
"""
 
# ---------------------------------------------------------------------------
# Report endpoints (Solenso)
# ---------------------------------------------------------------------------
 
API_POWER_BY_STATION: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm-report/report_select_power_by_station"
)
"""POST endpoint for per-station power data in 15-minute intervals.
 
Returns detailed intra-day power readings (PV, consumption, grid, BMS)
for a single station on a given day, one entry per 15-minute slot.
"""
 
API_OEM_EQ: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm-report/oem_eq_p_c_1"
)
"""POST endpoint for the OEM daily PV energy list report.
 
Returns a paginated JSON response with one record per day in the requested
date range. Each record contains the station ID, owner name, timezone, date,
``pv_eq`` (daily PV energy in kWh), ``consumption_eq``, and auxiliary fields.
 
Request body::
 
    {
        "WAITING_PROMISE": false,
        "body": {
            "sid_list": [<station_id>],
            "mode": 1,
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "page": 1,
            "page_size": 10
        }
    }
 
Used by :class:`~mysolenso.services.reports.oempower.MySolensoOEMPower`.
"""
 
API_OEM_COUNT: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm-report/oem_count_eq_g_c_1"
)
"""POST endpoint for OEM aggregated PV and consumption energy totals.
 
Returns a single JSON object (no pagination) with ``total_pv_eq`` and
``total_consumption_eq`` summed over the requested date range.
 
Request body::
 
    {
        "WAITING_PROMISE": false,
        "body": {
            "sid_list": [<station_id>],
            "mode": 1,
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD"
        }
    }
 
Used by :class:`~mysolenso.services.reports.oempowercount.MySolensoOEMPowerCount`.
"""
 
 
API_STATION_INFO_DEVICE: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm/station_select_device_of_tree"
)
"""POST endpoint to retrieve the full device tree of a station.
 
Request body: ``{"body": {"id": <station_id>}, "WAITING_PROMISE": true}``.
Returns a hierarchical list of devices attached to the station (DTU and
microinverters), including serial numbers, firmware versions, and warning
status for each device.
 
Used by :class:`~mysolenso.services.stations.stationinfodev.MySolensoStationInfoDevice`.
"""
 
API_STATION_COUNT_DEVICE: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm/station_count_device"
)
"""POST endpoint to retrieve device counts for a station.
 
Request body: ``{"body": {"id": <station_id>}, "WAITING_PROMISE": true}``.
Returns a summary of device counts by type: DTUs, microinverters, repeaters,
meters, BMS units, and so on.
 
Used by :class:`~mysolenso.services.stations.countdevice.MySolensoStationCountDevice`.
"""

API_STATION_LAYOUT: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm/layout_select_all"
)

API_STATION_ARRAY: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm/array_select_all"
)

API_STATION_DATA_MODULE_DAY: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm-data/data_select_module_day_data"
)


API_DTU_SELECT_ALL: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm/dtu_select_all"
)
"""POST endpoint to retrieve the DTU and all associated microinverters for a station.
 
Request body: ``{"body": {"id": <station_id>}, "WAITING_PROMISE": true}``.
Returns the primary DTU record (id, sn, dev_type, vc) along with the complete
list of microinverters attached through the repeater layer.
 
Used by :class:`~mysolenso.services.dtu.selectall.MySolensoDTUSelectAll`.
"""
 
API_DTU_FIND: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm/dtu_find"
)
"""POST endpoint to retrieve detailed information about a single DTU.
 
Request body: ``{"body": {"id": <dtu_id>}, "WAITING_PROMISE": true}``.
Returns the complete DTU record including firmware versions, hardware model,
rule configuration, and the list of supported microinverter types.
 
Used by :class:`~mysolenso.services.dtu.find.MySolensoDTUFind`.
"""
 
API_MICRO_FIND: str = (
    BASE_URL_SOLENSO + "api/gateway/pvm/micro_find"
)
"""POST endpoint to retrieve detailed information about a single microinverter.
 
Request body: ``{"body": {"id": <micro_id>}, "WAITING_PROMISE": true}``.
Returns the complete microinverter record including serial number, firmware
versions, hardware model, port configuration, and connection/warning status.
 
Used by :class:`~mysolenso.services.micro.find.MySolensoMicroFind`.
"""
 
# ---------------------------------------------------------------------------
# Power / energy history endpoints (Hoymiles)
# ---------------------------------------------------------------------------
 
API_POWER_BY_DAY: str = BASE_URL_HOYMILES + "0/station/data/count_power_by_day"
"""POST endpoint for the intra-day grid power curve of a station (Hoymiles).
 
Request body: ``{"sid": <station_id>, "date": "YYYY-MM-DD"}``.
Returns a binary protobuf response containing ``HH:MM`` time labels and a
packed ``float32`` array of grid power values (Watts) sampled throughout
the day.
 
Used by :class:`~mysolenso.services.powerbyday.MySolensoPowerByDay`.
"""
 
API_POWER_DAY_OF_YEAR: str = (
    BASE_URL_HOYMILES + "0/station/data/count_eq_by_day_of_year"
)
"""POST endpoint for day-of-year energy production totals (Hoymiles).
 
Request body: ``{"sid": <station_id>}``.
Returns a mixed text/binary protobuf response with ``YYYY-MM-DD`` date strings
and a packed ``float32`` array of daily energy values (Wh) covering every day
since the station was commissioned.
 
Used by :class:`~mysolenso.services.dayofyeay.MySolensoCountByDayOfYeay`.
"""

API_POWER_PLAYBACK_BY_DAY: str = (
    BASE_URL_HOYMILES + "0/station/data/count_playback_power_by_day"
)

API_DOWN_MODULE_DAY_DATA: str = (
    BASE_URL_HOYMILES + "0/module/data/down_module_day_data"
)