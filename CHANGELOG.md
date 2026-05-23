# CHANGELOG

<!-- version list -->
## v1.3.1 (2026-05-23)
- Correction pytest: test 15, 21 and 22 change day,
- Force node24 for yaml (FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true).

## v1.3.0 (2026-05-23)
- Add Class MySolensoStationLayout,
- Add Class MySolensoStationArray,
- Add Class MySolensoPowerPlayBackByDay,
- Add Class MySolensoStationDataModuleDay,
- Add example_layout.py and example_powerbyday.py,
- Move all example_* to directory examples,
- Add pytest: test_26_station_layout.py, test_27_station_array.py, test_28_station_powerbyday.py and test_29_station_datamodule.py,
- Update README.md,
- Update documentation.

## v1.2.0 (2026-05-20)
- Update data for publication into pypi.org,
- Add Class MySolensoStationInfoDevice,
- Add Class MySolensoStationCountDevice,
- Add Class MySolensoStationAK,
- Add Class MySolensoDTUSelectAll,
- Add Class MySolensoDTUFind,
- Add Class MySolensoMicroFind,
- Add example_stations.py,
- Add example_dtu.py,
- Add example_micro.py
- Add pytest: test_01_post.py, test_16_service_dtu_selectall.py, test_17_service_dtu_find.py, test_18_service_micro_find.py, test_23_station_ak.py, test_24_station_countdevice and test_25_station_stationinfodev.py,
- Update documentation.

## v1.1.0 (2026-05-17)
- Add Class MySolensoPowerByStation,
- Add Class MySolensoOEMPower,
- Add Class MySolensoOEMPowerCount,
- Add example_reports.py,
- Update README.md,
- Rename old pytest: 
  - tests\test_solenso_api.py to tests\test_00_solenso_api.py
  - tests\test_service_me.py to tests\test_10_service_me.py
  - tests\test_service_station.py to tests\test_11_service_station.py
  - tests\test_service_stationdata.py to tests\test_12_service_stationdata.py
  - tests\test_service_stationcount.py to tests\test_13_service_stationcount.py
- Add pytest: test_20_report_powerbystation.py, test_14_service_dayofyear.py, 
    test_15_service_powerbyday.py, test_21_report_oempower.py and test_22_report_oempowercount.py

## v1.0.0 (2026-05-15)
- Update documentation,
- stationcount - Add function get_station_refresh to refresh station energy counters,
- powerbyday - Add function get_power_refresh to refresh station Power data,

## v0.0.1c0 (2026-05-15)
- Add Class MySolensoStationCount,
- Add Class MySolensoPowerByDay,
- Add Class MySolensoCountByDayOfYeay,
- Add pytest: test_service_me, test_service_station, test_service_stationdata and test_service_stationcount,
- Correction auth - function get_auth_headers_hoymiles,
- Correction me - None if empty value,
- Correction stationdata - change return type for install_power str to dict.


## v0.0.1b0 (2026-05-14)
- Add Run PyTest to build,
- Add class MySolensoStationData,
- Update documentation.

## v0.0.1a0 (2026-05-14)
- Initial Release.