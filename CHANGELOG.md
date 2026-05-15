# CHANGELOG

<!-- version list -->
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