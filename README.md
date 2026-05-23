# mysolenso

![PyPI](https://img.shields.io/pypi/v/mysolenso) ![TestPyPI](https://img.shields.io/badge/dynamic/json?label=TestPyPI&url=https%3A%2F%2Ftest.pypi.org%2Fpypi%2Fmysolenso%2Fjson&query=$.info.version) ![License](https://img.shields.io/pypi/l/mysolenso)

[![Docs](https://img.shields.io/badge/docs-online-brightgreen)](https://thanatos-vf-2000.github.io/mysolenso/) [![Workflow Status](https://github.com/thanatos-vf-2000/mysolenso/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/thanatos-vf-2000/mysolenso/actions)

![Python Versions](https://img.shields.io/pypi/pyversions/mysolenso)
![Downloads](https://img.shields.io/pypi/dm/mysolenso)

Python library for the [Solenso](https://monitor.solenso.net/platform/) photovoltaic monitoring platform.

The library handles authentication, user profile retrieval, PV station data, real-time energy counters, historical daily production, OEM reporting, DTU and microinverter management, physical panel layout, array configuration, power playback curves, and daily module data - all from a single `MySolenso` client object.

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
    - [`countbydayofyear` - Daily production history](#countbydayofyear---daily-production-history)
    - [`powerbystation` - Per-station 15-min power report](#powerbystation---per-station-15-min-power-report)
    - [`oempower` - OEM daily report (list)](#oempower---oem-daily-report-list)
    - [`oempowercount` - OEM aggregated totals](#oempowercount---oem-aggregated-totals)
    - [`stationinfodevice` - Device tree](#stationinfodevice---device-tree)
    - [`stationcountdevice` - Device count summary](#stationcountdevice---device-count-summary)
    - [`stationak` - Geographic information](#stationak---geographic-information)
    - [`dtuselectall` - DTU and microinverter list](#dtuselectall---dtu-and-microinverter-list)
    - [`dtufind` - Single DTU detail](#dtufind---single-dtu-detail)
    - [`microfind` - Single microinverter detail](#microfind---single-microinverter-detail)
    - [`stationlayout` - Physical panel layout](#stationlayout---physical-panel-layout)
    - [`stationarray` - Array configuration](#stationarray---array-configuration)
    - [`powerplaybackbyday` - Power playback curve](#powerplaybackbyday---power-playback-curve)
    - [`stationdatamodule` - Daily module data descriptor](#stationdatamodule---daily-module-data-descriptor)
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

# Account owner name
print(client.me.name)

# Today's total energy production (kWh)
print(client.stationcount.today_eq)

# Intra-day power curve (Watts, 15-min intervals)
data = client.powerbyday.get_data
print(data["date"], data["values"])

# Full production history (Wh per day since commissioning)
history = client.countbydayofyear.get_data
print(history["2026-01-01"])  # e.g. 3241.5

# OEM energy totals for a date range
client.oempowercount.set_day("2026-04-01", "2026-04-30")
print(client.oempowercount.total_pv)   # e.g. "415.72"

# Physical panel layout
client.stationlayout.station_layout_refresh()
for dtu in client.stationlayout.list_dtu:
    print(dtu["dtu_sn"])
    for panel in client.stationlayout.get_mi_info_by_dtu(dtu["dtu_id"]):
        print("  port", panel["port"], "@ x=%i y=%i" % (panel["x"], panel["y"]))

# Power playback curve (Hoymiles)
client.powerplaybackbyday.get_power_refresh()
for time, watts in client.powerplaybackbyday.get_data["values"].items():
    print(time, "->", watts, "W")
```

---

## Services

All services are instantiated automatically by `MySolenso` and are accessible as attributes on the client object.

### `me` - User profile

```python
print(client.me.name)   # account display name
print(client.me.email)  # account e-mail
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

Detailed technical configuration of the active station (inverter model, installed capacity, timezone, pricing, etc.).

```python
info = client.stationdata.station_data
print(info["capacity"])
```

### `stationcount` - Real-time counters

Real-time and cumulative energy counters for the active station.

```python
print(client.stationcount.today_eq)   # today's production (kWh)
print(client.stationcount.total_eq)   # all-time total (kWh)
print(client.stationcount.co2)        # CO₂ offset (kg)
print(client.stationcount.real_power) # current output (W)
```

### `powerbyday` - Intra-day power curve

Grid power measurements (Watts) sampled in 15-minute intervals throughout a single day (Hoymiles endpoint).

```python
result = client.powerbyday.get_data
# {"date": "2026-05-15", "values": {"08:00": 512.0, "08:15": 634.5, ...}}

# Query a specific date
client.powerbyday.set_day("2025-12-25")
print(client.powerbyday.get_data["values"])

# Refresh without changing the date
client.powerbyday.get_power_refresh()
```

### `countbydayofyear` - Daily production history

Complete daily PV energy production (Wh) since the station was commissioned.

```python
history = client.countbydayofyear.get_data
# {"2025-06-01": 28612.5, "2025-06-02": 31072.0, ...}

from datetime import date
print(history.get(str(date.today()), "N/A"))
```

### `powerbystation` - Per-station 15-min power report

Per-station power data in 15-minute intervals for a single day (PV, consumption, grid, BMS).

```python
client.powerbystation.set_day("2026-05-01")
for record in client.powerbystation.all_data:
    print(record["time"], record["pv_power"])
```

### `oempower` - OEM daily report (list)

Daily PV energy production records from the Solenso OEM endpoint, one record per day.

```python
client.oempower.set_day("2026-04-01", "2026-04-30")

for record in client.oempower.all_data:
    print(record["date"], record["pv_eq"], "kWh")

# Simplified {date, power} view
for entry in client.oempower.power_data:
    print(entry["date"], entry["power"])

client.oempower.oem_pv_refresh()
```

Each record contains: `sid`, `name`, `tz_name`, `date`, `pv_eq`, `consumption_eq`, `meter_c_eq`, `meter_location`, `capacitor`, `create_at`, `p2g`, `lfg`, `eq_hour`.

### `oempowercount` - OEM aggregated totals

Aggregated PV and consumption energy totals for the active station over a date range (single API call, no pagination).

```python
client.oempowercount.set_day("2026-04-01", "2026-04-30")

print(client.oempowercount.total_pv)          # "415.72" (kWh)
print(client.oempowercount.total_consumption)  # "0" (kWh)

client.oempowercount.oem_power_refresh()
```

### `stationinfodevice` - Device tree

Full hierarchical device tree for the active station: DTU and all attached microinverters with serial numbers, firmware versions, and connectivity status.

```python
client.stationinfodevice.station_info_device_refresh()
print(client.stationinfodevice.all_data)
```

### `stationcountdevice` - Device count summary

Device count summary by type (DTU, microinverters, repeaters, meters, BMS, etc.).

```python
print(client.stationcountdevice.dtu_num)  # number of DTUs
print(client.stationcountdevice.mi_num)   # number of microinverters
```

### `stationak` - Geographic information

Geographic and address information for the active station.

```python
print(client.stationak.longitude)
print(client.stationak.latitude)
print(client.stationak.address)
```

### `dtuselectall` - DTU and microinverter list

DTU and associated microinverter list for the active station.

```python
client.dtuselectall.dtu_select_all_refresh()
print(client.dtuselectall.dtu_sn)        # master DTU serial number

for micro in client.dtuselectall.list_micros_info:
    print(micro["sn"], micro["id"])
```

### `dtufind` - Single DTU detail

Full record for a single DTU including firmware versions, hardware model, and rule configuration.

```python
client.dtufind.set_dtu(dtu_id=1456060)
print(client.dtufind.all_data)
```

### `microfind` - Single microinverter detail

Full record for a single microinverter including serial number, firmware, port configuration, and warning status.

```python
client.microfind.set_micro(micro_id=6699010)
print(client.microfind.all_data)
```

### `stationlayout` - Physical panel layout

Physical placement of every microinverter panel for the active station. Each record maps a DTU + microinverter port to a grid position (x, y) in the installation diagram.

```python
client.stationlayout.station_layout_refresh()

# List unique DTUs
for dtu in client.stationlayout.list_dtu:
    print("DTU %i - %s" % (dtu["dtu_id"], dtu["dtu_sn"]))

    # Panels attached to this DTU, sorted by position
    for panel in client.stationlayout.get_mi_info_by_dtu(dtu["dtu_id"]):
        print("  SN %s port %i @ x=%i y=%i" % (
            panel["sn"], panel["port"], panel["x"], panel["y"]
        ))

# Switch station
client.stationlayout.set_station(station_id=43)
```

### `stationarray` - Array configuration

Solar panel array geometry for the active station: tilt angle, orientation, row/column dimensions, pattern, and grid offsets.

```python
client.stationarray.station_array_refresh()

print(client.stationarray.name)        # array / owner name
print(client.stationarray.angle_tilt)  # tilt in degrees
print(client.stationarray.orientation) # azimuth code
print(client.stationarray.column)      # number of columns
print(client.stationarray.row)         # number of rows
```

### `powerplaybackbyday` - Power playback curve

Intra-day power playback curve (Hoymiles). Returns instantaneous Watt readings keyed by `HH:MM` time labels. Defaults to today (or yesterday before 01:00 to avoid empty data).

```python
# Refresh with today's data
client.powerplaybackbyday.get_power_refresh()

result = client.powerplaybackbyday.get_data
# {"date": "2026-05-23", "values": {"06:00": 26.6, "06:15": 63.4, ...}}

for time, watts in result["values"].items():
    print(time, "->", watts, "W")

# Query a specific date
client.powerplaybackbyday.set_day("2026-05-20")
print(client.powerplaybackbyday.get_data["values"])

# Switch station
client.powerplaybackbyday.set_station_id(43)
```

### `stationdatamodule` - Daily module data descriptor

Download descriptor (URL and HTTP method) for the raw daily module binary data file produced by Hoymiles for the active station. Use the returned `full_url` to fetch the binary file with a separate request.

```python
client.stationdatamodule.station_data_module_day_refresh()

print(client.stationdatamodule.sid)       # station id
print(client.stationdatamodule.url)       # relative download path
print(client.stationdatamodule.full_url)  # absolute URL ready to fetch

# Query a specific date
client.stationdatamodule.set_day("2026-05-20")
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
| `tests/test_01_post.py` | HTTP POST helper |
| `tests/test_10_service_me.py` | User profile service |
| `tests/test_11_service_station.py` | Station list service |
| `tests/test_12_service_stationdata.py` | Station data service |
| `tests/test_13_service_stationcount.py` | Real-time counters |
| `tests/test_14_service_dayofyear.py` | Daily production history |
| `tests/test_15_service_powerbyday.py` | Intra-day power curve |
| `tests/test_16_service_dtu_selectall.py` | DTU and microinverter list |
| `tests/test_17_service_dtu_find.py` | Single DTU detail |
| `tests/test_18_service_micro_find.py` | Single microinverter detail |
| `tests/test_20_report_powerbystation.py` | Per-station power report |
| `tests/test_21_report_oempower.py` | OEM daily list report |
| `tests/test_22_report_oempowercount.py` | OEM aggregated totals |
| `tests/test_23_station_ak.py` | Station geographic / AK data |
| `tests/test_24_station_countdevice.py` | Device count summary |
| `tests/test_25_station_stationinfodev.py` | Station device tree |
| `tests/test_26_station_layout.py` | Physical panel layout (`MySolensoStationLayout`) |
| `tests/test_27_station_array.py` | Array configuration (`MySolensoStationArray`) |
| `tests/test_28_station_powerbyday.py` | Power playback curve (`MySolensoPowerPlayBackByDay`) |
| `tests/test_29_station_datamodule.py` | Daily module data descriptor (`MySolensoStationDataModuleDay`) |

---

## Example scripts

### Generic example

```bash
PYTHONPATH=./src/ python3 examples/example.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example.py`](./examples/example.py) for a full walkthrough of the basic services.

Result:

```text
INFO:__main__:Start MySolensoAuth password...
===================================
Connected          : True
Token              : 3.KtqvJHpN7BxR4mLFWpDsaYtrwQZuocgjHe8n52vFxl9zUdCgPiwrETakJzCSGXoVRmLf7NQYdy6TKPXAbnJrWe.0
Headers - hoymiles : {'Authorization': '3.KtqvJHpN7BxR4mLFWpDsaYtrwQZuocgjHe8n52vFxl9zUdCgPiwrETakJzCSGXoVRmLf7NQYdy6TKPXAbnJrWe.0'}
Headers - solenso  : {'Cookie': 'solenso_token_language=fr_fr; solenso_token=3.KtqvJHpN7BxR4mLFWpDsaYtrwQZuocgjHe8n52vFxl9zUdCgPiwrETakJzCSGXoVRmLf7NQYdy6TKPXAbnJrWe.0'}
===================================
INFO:__main__:End MySolensoAuth.
INFO:__main__:Start MySolenso...
===================================
Connected          : True
Token              : 3.KtqvJHpN7BxR4mLFWpDsaYtrwQZuocgjHe8n52vFxl9zUdCgPiwrETakJzCSGXoVRmLf7NQYdy6TKPXAbnJrWe.0
Headers - hoymiles : {'Authorization': '3.KtqvJHpN7BxR4mLFWpDsaYtrwQZuocgjHe8n52vFxl9zUdCgPiwrETakJzCSGXoVRmLf7NQYdy6TKPXAbnJrWe.0'}
Headers - solenso  : {'Cookie': 'solenso_token_language=fr_fr; solenso_token=3.KtqvJHpN7BxR4mLFWpDsaYtrwQZuocgjHe8n52vFxl9zUdCgPiwrETakJzCSGXoVRmLf7NQYdy6TKPXAbnJrWe.0'}
===================================
me - username : JDOE
me - name     : John Doe
===================================
station - id : 1234567
station - ak : aP9kGrfAzvTe41dR2R1kjfWlldns
===================================
stationdata - id                : 1234567
stationdata - money_unit        : EUR
stationdata - electricity_price : 0.25
===================================
stationcount - capacitor : 5
stationcount - today_eq : 13035.0
stationcount - month_eq : 418054
===================================
powerbyday - get_data : {'metric': 'grid_power', 'date': '2026-05-23', 'values': {'00:00': 0.0, '01:00': 0.0, '02:00': 0.0, '03:00': 0.0, '04:00': 0.0, '05:00': 0.0, '06:00': 25.6, '06:15': 60.3, ..., '13:45': 3622.8, '14:00': 3659.0}}
powerbyday - get_data : {'metric': 'grid_power', 'date': '2026-05-22', 'values': {'06:30': 80.0, '06:45': 106.6, ..., '12:00': 2915.9, '12:15': 3043.3, ..., '16:45': 3356.9, '17:00': 3072.1, '17:15': 2769.6, '17:30': 2632.1, '17:45': 2644.4, '18:00': 2507.4, '18:15': 2377.5, '18:30': 2258.7, '18:45': 1813.6, ..., '23:30': 0.0}}
===================================
countbydayofyear - get_data : {'2025-06-01': 25928.0, '2025-06-02': 28562.0, ...,'2026-05-22': 30212.0, '2026-05-23': 0.0}
INFO:__main__:End MySolenso.
```

---

### Report example

```bash
PYTHONPATH=./src/ python3 examples/example_reports.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_reports.py`](./examples/example_reports.py) for OEM report usage.

Result:

```text
INFO:__main__:Start MySolenso...
===================================
Power by Station
name          : DOE JONH
06:00     :     26
06:15     :     60
06:30     :    105
06:45     :    143
07:00     :    165
07:15     :    204
07:30     :    258
07:45     :    296
08:00     :    381
08:15     :    389
===================================
OEM Power
2026-04-11     :        6.8 KwH
2026-04-12     :      16.98 KwH
2026-04-13     :      20.42 KwH
2026-04-14     :      26.69 KwH
2026-04-15     :      18.08 KwH
===================================
OEM Power Count
Total pv         :      88.97 KwH
Total consumption:          0 KwH
INFO:__main__:End MySolenso.
```

---

### Stations example

```bash
PYTHONPATH=./src/ python3 examples/example_stations.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_stations.py`](./examples/example_stations.py) for station device tree, device count, and geographic info usage.

Result:

```text
INFO:__main__:Starting MySolenso...
===================================
Station Info Device
SN Master          : D0900099H
DTU list:
SN:       A99001X1A
SN:       A99001X1B
SN:       A99001X1C
SN:       A99001X1D
SN:       A99001X1E
DTU info:
SN:       A99001X1A - DTU   D0900099H - MODEL      Sol-H1000H
SN:       A99001X1B - DTU   D0900099H - MODEL      Sol-H1000H
SN:       A99001X1C - DTU   D0900099H - MODEL      Sol-H1000H
SN:       A99001X1D - DTU   D0900099H - MODEL      Sol-H1000H
SN:       A99001X1E - DTU   D0900099H - MODEL      Sol-H1000H
Station Count Device
station_num: 1
===================================
Station AK: aP9kGrfAzvTe41dR2R1kjfWlldns
address: 95 Moon Road, 99999 Galaxy, World
INFO:__main__:MySolenso finished.
```

---

### DTU example

```bash
PYTHONPATH=./src/ python3 examples/example_dtu.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_dtu.py`](./examples/example_dtu.py) for DTU select-all and single-DTU detail usage.

Result:

```text
INFO:__main__:Starting MySolenso...
===================================
DTU Select All
SN Master          : D0900099H
Micros list:
SN:       A99001X1E - vc:   2BD - ID:    6699010
SN:       A99001X1D - vc:   23D - ID:    6699020
SN:       A99001X1C - vc:   212 - ID:    6699030
SN:       A99001X1B - vc:   22L - ID:    6699040
SN:       A99001X1A - vc:   2L2 - ID:    6699050
Station Count Device
station_num: 1
===================================
DTU find
station_name:     DOE JONH
INFO:__main__:MySolenso finished.
```

---

### Micro example

```bash
PYTHONPATH=./src/ python3 examples/example_micro.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_micro.py`](./examples/example_micro.py) for single microinverter detail usage.

Result:

```text
INFO:__main__:Starting MySolenso...
===================================
Micro Find
ID: 6699050
station_name:     DOE JONH
INFO:__main__:MySolenso finished.
```

---

### Layout example

```bash
PYTHONPATH=./src/ python3 examples/example_layout.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_layout.py`](./examples/example_layout.py) for station panel layout and array configuration usage.

Result:

```text
INFO:__main__:Starting MySolenso...
===================================
Station Layout
SN Master          : D0900099H
DTU 1456060 - D0900099H
- ID 6699010 SN A99001X1E: port 1 [x: 0 - y: 0]
- ID 6699010 SN A99001X1E: port 2 [x: 0 - y: 1]
- ID 6699020 SN A99001X1D: port 1 [x: 0 - y: 2]
- ID 6699020 SN A99001X1D: port 2 [x: 0 - y: 3]
- ID 6699030 SN A99001X1C: port 1 [x: 0 - y: 4]
- ID 6699030 SN A99001X1C: port 2 [x: 0 - y: 5]
- ID 6699040 SN A99001X1B: port 1 [x: 0 - y: 8]
- ID 6699040 SN A99001X1B: port 2 [x: 0 - y: 9]
===================================
Station Array
Name:  DOE JONH
angle_tilt:  20
INFO:__main__:MySolenso finished.
```

---

### Power by day example

```bash
PYTHONPATH=./src/ python3 examples/example_powerbyday.py --username <USER> --password <PASSWORD_CRYPT>
```

See [`example_powerbyday.py`](./examples/example_powerbyday.py) for power playback curve and daily module data descriptor usage.

Result:

```text
INFO:__main__:Starting MySolenso...
===================================
Station Data module
URL:  https://monitor.solenso.net/platform//api/0/module/data/down_module_day_data
===================================
Station Power by day
Day : 2026-05-23
2026-05-23 00:00 -> 0.0
...
2026-05-23 06:00 -> 26.6
2026-05-23 06:15 -> 63.4
2026-05-23 06:30 -> 110.3
2026-05-23 06:45 -> 151.1
2026-05-23 07:00 -> 173.7
...
2026-05-23 09:45 -> 1260.7
...
2026-05-23 14:15 -> 3883.3
...
INFO:__main__:MySolenso finished.
```

---

## Documentation

Full API documentation is available at **[thanatos-vf-2000.github.io/mysolenso](https://thanatos-vf-2000.github.io/mysolenso/)**.

---

## Help

You must use your encrypted password or a token, not your plain-text password. To generate the encrypted credential, use the [pwdsolenso](https://github.com/thanatos-vf-2000/pwdsolenso) project.

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
