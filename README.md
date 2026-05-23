# mysolenso

![PyPI](https://img.shields.io/pypi/v/mysolenso) ![TestPyPI](https://img.shields.io/badge/dynamic/json?label=TestPyPI&url=https%3A%2F%2Ftest.pypi.org%2Fpypi%2Fmysolenso%2Fjson&query=$.info.version) ![License](https://img.shields.io/pypi/l/mysolenso)

[![Docs](https://img.shields.io/badge/docs-online-brightgreen)](https://thanatos-vf-2000.github.io/mysolenso/) [![Workflow Status](https://github.com/thanatos-vf-2000/mysolenso/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/thanatos-vf-2000/mysolenso/actions)

![Python Versions](https://img.shields.io/pypi/pyversions/mysolenso)
![Downloads](https://img.shields.io/pypi/dm/mysolenso)

Python library for the [Solenso](https://monitor.solenso.net/platform/) photovoltaic monitoring platform.

The library handles authentication, user profile retrieval, PV station data, real-time energy counters, historical daily production, and OEM reporting - all from a single `MySolenso` client object.

> **Note:** The project is independent of Solenso. You must use your **encrypted** password or a token, not your plain-text password. Use [pwdsolenso](https://github.com/thanatos-vf-2000/pwdsolenso) to obtain the encrypted credential.

---

## Table of contents

- [mysolenso](#mysolenso)
  - [Table of contents](#table-of-contents)
  - [https://www.solenso.fr/ - mysolenso](#httpswwwsolensofr---mysolenso)
  - [Installation](#installation)
  - [Authentication](#authentication)
  - [Quick start](#quick-start)
  - [Services](#services)
    - [`me` - User profile](#me---user-profile)
    - [`station` - Station list](#station---station-list)
    - [`stationdata` - Station configuration](#stationdata---station-configuration)
    - [`stationcount` - Real-time counters](#stationcount---real-time-counters)
    - [`powerbyday` - Intra-day power curve](#powerbyday---intra-day-power-curve)
    - [`day_of_year` - Daily production history](#day_of_year---daily-production-history)
    - [`oem_power` - OEM daily report (list)](#oem_power---oem-daily-report-list)
    - [`oem_power_count` - OEM aggregated totals](#oem_power_count---oem-aggregated-totals)
  - [Error handling](#error-handling)
  - [Running the tests](#running-the-tests)
  - [Example scripts](#example-scripts)
    - [Generic example](#generic-example)
    - [Report example](#report-example)
    - [Stations example](#stations-example)
    - [DTU example](#dtu-example)
    - [Micro example](#micro-example)
    - [Layout example](#layout-example)
    - [Power by day example](#power-by-day-example)
  - [Documentation](#documentation)
  - [Help](#help)
  - [Contributing](#contributing)
  - [Issues](#issues)
  - [License](#license)

---

## https://www.solenso.fr/ - mysolenso

This library can read information from https://monitor.solenso.net/platform/. The project is independent of Solenso.

---

## Installation

```bash
pip install mysolenso
```

The library requires **Python 3.10+** and has no mandatory third-party runtime dependencies beyond the standard library and `requests`.

---

## Authentication

You need two pieces of information:

| Parameter  | Description |
|------------|-------------|
| `username` | Your Solenso account e-mail address. |
| `password` | Your **encrypted** password (from [pwdsolenso](https://github.com/thanatos-vf-2000/pwdsolenso)), **or** |
| `token`    | A pre-obtained API token (skip `password` when using this). |

```python
from mysolenso import MySolenso

# Option A - with encrypted password
client = MySolenso(username="jdoe", password="encrypted_pass")

# Option B - with a token
client = MySolenso(username="jdoe", token="your_api_token")
```

---

## Quick start

```python
from mysolenso import MySolenso

client = MySolenso(username="jdoe", password="encrypted_pass")

# Display the account owner name
print(client.me.name)

# Today's total energy production (kWh)
print(client.stationcount.today_eq)

# Intra-day power curve (Watts, 15-min intervals)
data = client.powerbyday.get_data
print(data["date"], data["values"])

# Full production history (Wh per day since commissioning)
history = client.day_of_year.get_data
print(history["2026-01-01"])  # e.g. 3241.5

# OEM energy totals for a date range
client.oem_power_count.set_day("2026-04-01", "2026-04-30")
print(client.oem_power_count.total_pv)   # e.g. "415.72"
```

---

## Services

All services are instantiated automatically by `MySolenso` and are accessible as attributes on the client object.

### `me` - User profile

```python
print(client.me.name)       # account display name
print(client.me.email)      # account e-mail
```

### `station` - Station list

```python
# List all stations linked to the account
for s in client.station.stations:
    print(s["id"], s["name"])

# Switch the active station (all other services follow)
client.station.set_station(station_id=43)
```

### `stationdata` - Station configuration

Detailed technical configuration of the active station (inverter model, capacity, timezone, etc.).

```python
info = client.stationdata.station_data
print(info["capacity"])
```

### `stationcount` - Real-time counters

Real-time and cumulative energy counters for the active station.

```python
print(client.stationcount.today_eq)    # today's production (kWh)
print(client.stationcount.total_eq)    # all-time total (kWh)
print(client.stationcount.co2)         # CO₂ offset (kg)
```

### `powerbyday` - Intra-day power curve

Grid power measurements (Watts) sampled in 15-minute intervals throughout a single day.

```python
result = client.powerbyday.get_data
# {
#   "metric": "grid_power",
#   "date":   "2026-05-15",
#   "values": {"08:00": 512.0, "08:30": 1024.5, ...}
# }

# Query a specific date
client.powerbyday.set_day("2025-12-25")
print(client.powerbyday.get_data["values"])

# Refresh without changing the date
client.powerbyday.get_power_refresh()
```

### `day_of_year` - Daily production history

Complete daily PV energy production (Wh) since the station was commissioned.

```python
history = client.day_of_year.get_data
# {"2025-06-01": 28612.5, "2025-06-02": 31072.0, ..., "2026-05-15": 0.0}

# Days with 0 Wh (cloudy days, current day before sunset) are included
from datetime import date
print(history.get(str(date.today()), "N/A"))

# Switch station
client.day_of_year.set_station_id(43)
```

### `oem_power` - OEM daily report (list)

Daily PV energy production records from the Solenso OEM endpoint, one record per day.

```python
# Fetch records for April 2026
client.oem_power.set_day("2026-04-01", "2026-04-30")

# Full records (all API fields)
for record in client.oem_power.all_data:
    print(record["date"], record["pv_eq"], "kWh")

# Simplified {date, power} view
for entry in client.oem_power.power_data:
    print(entry["date"], entry["power"])

# Refresh data
client.oem_power.oem_pv_refresh()
```

Each record contains: `sid`, `name`, `tz_name`, `date`, `pv_eq`, `consumption_eq`, `meter_c_eq`, `meter_location`, `capacitor`, `create_at`, `p2g`, `lfg`, `eq_hour`.

### `oem_power_count` - OEM aggregated totals

Aggregated PV and consumption energy totals for the active station over a date range (single API call, no pagination).

```python
client.oem_power_count.set_day("2026-04-01", "2026-04-30")

print(client.oem_power_count.total_pv)           # "415.72" (kWh)
print(client.oem_power_count.total_consumption)   # "0" (kWh, or actual value)
print(client.oem_power_count.all_data)            # raw dict

# Refresh
client.oem_power_count.oem_power_refresh()
```

---

## Error handling

All library errors inherit from `MySolensoException`:

```python
from mysolenso import (
    MySolenso,
    MySolensoException,
    MySolensoAuthenticationException,
    MySolensoConnectionException,
)

try:
    client = MySolenso(username="jdoe", password="wrong_pass")
except MySolensoAuthenticationException as e:
    print("Bad credentials:", e)
except MySolensoConnectionException as e:
    print("Connection problem:", e)
except MySolensoException as e:
    print("General library error:", e)
```

| Exception | When raised |
|-----------|-------------|
| `MySolensoException` | Base class - catches everything. |
| `MySolensoConnectionException` | Invalid arguments (empty username, missing credentials) or network issue before the request. |
| `MySolensoAuthenticationException` | API returned an error status, unexpected message, or token was absent from the response. |

---

## Running the tests

Tests require `pytest`. Install the package in editable mode first:

```bash
pip install -e ".[dev]"
# or just:
pip install pytest

PYTHONPATH=./src pytest tests/ -v
```

Test files:

| File | Covers |
|------|--------|
| `tests/test_00_solenso_api.py` | Authentication and core API |
| `tests/test_10_service_me.py` | User profile service |
| `tests/test_11_service_station.py` | Station list service |
| `tests/test_12_service_stationdata.py` | Station data service |
| `tests/test_13_service_stationcount.py` | Real-time counters |
| `tests/test_14_service_dayofyear.py` | Daily production history |
| `tests/test_15_service_powerbyday.py` | Intra-day power curve |
| `tests/test_16_service_dtu_selectall.py` |  DTU and microinverter list service |
| `tests/test_17_service_dtu_find.py` | single DTU detail service |
| `tests/test_18_service_micro_find.py` | single microinverter detail service |
| `tests/test_20_report_powerbystation.py` | Per-station power report |
| `tests/test_21_report_oempower.py` | OEM daily list report |
| `tests/test_22_report_oempowercount.py` | OEM aggregated totals |
| `tests/test_23_station_ak.py` | station geolocation/AK data service |
| `tests/test_24_station_countdevice.py` | retrieving device count summary data for a station |
| `tests/test_25_station_stationinfodev.py` | station geolocation/AK data service |

---

## Example scripts

### Generic example

```bash
PYTHONPATH=./src/ python3 example.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example.py`](./example.py) for a full walkthrough of the basic services.

### Report example

```bash
PYTHONPATH=./src/ python3 example_reports.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_reports.py`](./example_reports.py) for OEM report usage.

---

### Stations example

```bash
PYTHONPATH=./src/ python3 example_stations.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_stations.py`](./example_stations.py) for Stations report usage.

---

### DTU example

```bash
PYTHONPATH=./src/ python3 example_dtu.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_dtu.py`](./example_dtu.py) for DTU report usage.

---

### Micro example

```bash
PYTHONPATH=./src/ python3 example_micro.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_micro.py`](./example_micro.py) for DTU report usage.

---

### Layout example

```bash
PYTHONPATH=./src/ python3  example_layout.py --username <USER> --password <PASSWORD_CRYPT>
```

See [` example_layout.py`](./ example_layout.py) for Layout report usage.

---

### Power by day example

```bash
PYTHONPATH=./src/ python3  example_powerbyday.py --username <USER> --password <PASSWORD_CRYPT>
```

See [` example_powerbyday.py`](./ example_powerbyday.py) for Layout report usage.

---

## Documentation

Full API documentation is available at **[thanatos-vf-2000.github.io/mysolenso](https://thanatos-vf-2000.github.io/mysolenso/)**.

---

## Help

You must use your crypt password or a token, not your password directly. To do this, use the project [pwdsolenso](https://github.com/thanatos-vf-2000/pwdsolenso).

---

## Contributing

Contributions of all kinds are welcome. Please read the [contributing guide](CONTRIBUTING.md) for development workflows and coding conventions.

[Issues ➡️](https://github.com/thanatos-vf-2000/mysolenso/issues)

---

## Issues

You can create issues in this repository to plan, discuss, and track work. Issues can track bug reports, new features and ideas, and anything else you need to write down or discuss. [➡️ Go to issues ⬅️](https://github.com/thanatos-vf-2000/mysolenso/issues)


---

## License

Copyright 2026 @Franck VANHOUCKE

Licensed under the [Apache License, Version 2.0](LICENSE).

> Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
