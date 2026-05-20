"""Tests for MySolensoStationInfoDevice - station geolocation/AK data service."""
 
import pytest
from unittest.mock import MagicMock, patch
 
from mysolenso.services.stations.stationinfodev import MySolensoStationInfoDevice
from mysolenso.exceptions import MySolensoException
 
 
# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
 
FULL_RESPONSE = [{
                "sn": "AABBCCDD",
                "warn_data": {
                    "_rw": "",
                    "connect": True,
                    "warn": False
                },
                "id": 1456060,
                "vc": "289",
                "dtu_sn": "AABBCCDD",
                "type": 1,
                "version": 3,
                "replace_num": 0,
                "model_no": "HD-Insight",
                "soft_ver": "V00.00.06",
                "hard_ver": "H12.02.02",
                "extend_data": {},
                "children": [
                    {
                        "sn": "ABCDEF01",
                        "warn_data": {
                            "warn": False,
                            "connect": True
                        },
                        "id": 7454520,
                        "vc": "2L2",
                        "dtu_sn": "AABBCCDD",
                        "type": 3,
                        "version": 3,
                        "replace_num": 0,
                        "model_no": "Sol-H1000H",
                        "soft_ver": "V01.00.04",
                        "hard_ver": "H00.04.00",
                        "extend_data": {
                            "dmt": 0,
                            "grid_name": "",
                            "route": 0,
                            "port_array": [
                                1,
                                2
                            ],
                            "grid_id": 0,
                            "grid_version": ""
                        },
                        "children": []
                    },
                    {
                        "sn": "ABCDEF02",
                        "warn_data": {
                            "warn": False,
                            "connect": True
                        },
                        "id": 6654200,
                        "vc": "22L",
                        "dtu_sn": "AABBCCDD",
                        "type": 3,
                        "version": 3,
                        "replace_num": 0,
                        "model_no": "Sol-H1000H",
                        "soft_ver": "V01.00.04",
                        "hard_ver": "H00.04.00",
                        "extend_data": {
                            "dmt": 0,
                            "grid_name": "",
                            "route": 0,
                            "port_array": [
                                1,
                                2
                            ],
                            "grid_id": 0,
                            "grid_version": ""
                        },
                        "children": []
                    },
                    {
                        "sn": "ABCDEF03",
                        "warn_data": {
                            "warn": False,
                            "connect": True
                        },
                        "id": 6654210,
                        "vc": "212",
                        "dtu_sn": "AABBCCDD",
                        "type": 3,
                        "version": 3,
                        "replace_num": 0,
                        "model_no": "Sol-H1000H",
                        "soft_ver": "V01.00.04",
                        "hard_ver": "H00.04.00",
                        "extend_data": {
                            "dmt": 0,
                            "grid_name": "",
                            "route": 0,
                            "port_array": [
                                1,
                                2
                            ],
                            "grid_id": 0,
                            "grid_version": ""
                        },
                        "children": []
                    }
                ]
            }]
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _make_parent(station_id=42, ak="ak_abc", stations=None):
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.stationinfodev = ak
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=tok"}
    return parent
 
 
def _make_station_infodev(api_response=None) -> MySolensoStationInfoDevice:
    parent = _make_parent()
    response = api_response if api_response is not None else FULL_RESPONSE
    with patch("mysolenso.services.stations.stationinfodev.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoStationInfoDevice(parent)
        obj._get_station_info_device()
        return obj
 
 
# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
 
def test_init_raises_when_no_station():
    """MySolensoStationInfoDevice raises if no active station is set."""
    parent = _make_parent(station_id=None)
    with pytest.raises(MySolensoException):
        MySolensoStationInfoDevice(parent)
 
 
def test_init_stores_station_id():
    parent = _make_parent(station_id=42)
    obj = MySolensoStationInfoDevice(parent)
    assert obj._station_id == 42
 

 
# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
 
def test_all_data():
    obj = _make_station_infodev()
    assert obj.all_data == FULL_RESPONSE[0]
 
 
def test_sn():
    obj = _make_station_infodev()
    assert obj.sn == "AABBCCDD"
 
def test_connect():
    obj = _make_station_infodev()
    assert obj.connect == True

def test_warn():
    obj = _make_station_infodev()
    assert obj.warn == False

def test_vc():
    obj = _make_station_infodev()
    assert obj.vc == "289"

def test_dtu_sn():
    obj = _make_station_infodev()
    assert obj.dtu_sn == "AABBCCDD"

def test_type():
    obj = _make_station_infodev()
    assert obj.type == 1

def test_version():
    obj = _make_station_infodev()
    assert obj.version == 3

def test_replace_num():
    obj = _make_station_infodev()
    assert obj.replace_num == 0

def test_model_no():
    obj = _make_station_infodev()
    assert obj.model_no == "HD-Insight"

def test_soft_ver():
    obj = _make_station_infodev()
    assert obj.soft_ver == "V00.00.06"

def test_hard_ver():
    obj = _make_station_infodev()
    assert obj.hard_ver == "H12.02.02"

# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------
 
def test_set_station_invalid_raises():
    """set_station raises when the station ID is not in the account list."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}])
    with patch("mysolenso.services.stations.stationinfodev.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationInfoDevice(parent)
        obj._get_station_info_device()
        with pytest.raises(MySolensoException):
            obj.set_station(id=999, refresh=False)
 
 
def test_set_station_updates_id_and_ak():
    """set_station stores the new station ID and AK key."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
    with patch("mysolenso.services.stations.stationinfodev.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationInfoDevice(parent)
        obj._get_station_info_device()
        obj.set_station(id=43, refresh=False)
        assert obj._station_id == 43
 
 
def test_set_station_with_refresh_calls_api():
    """set_station with refresh=True triggers a new API call."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
    with patch("mysolenso.services.stations.stationinfodev.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationInfoDevice(parent)
        obj._get_station_info_device()
        initial_count = MockPost.return_value.post.call_count
        obj.set_station(id=43, refresh=True)
        assert MockPost.return_value.post.call_count > initial_count
 
 
# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------
 
def test_station_info_device_refresh_calls_api():
    parent = _make_parent()
    with patch("mysolenso.services.stations.stationinfodev.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationInfoDevice(parent)
        obj._get_station_info_device()
        obj.station_info_device_refresh()
        assert MockPost.return_value.post.call_count >= 1
 
 
# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
 
def test_empty_response_raises():
    parent = _make_parent()
    with patch("mysolenso.services.stations.stationinfodev.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = {}
        obj = MySolensoStationInfoDevice(parent)
        with pytest.raises(MySolensoException):
            obj._get_station_info_device()
 
 
def test_network_error_raises():
    parent = _make_parent()
    with patch("mysolenso.services.stations.stationinfodev.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("connection error")
        obj = MySolensoStationInfoDevice(parent)
        with pytest.raises(MySolensoException):
            obj._get_station_info_device()
 
 
def test_headers_injected():
    parent = _make_parent()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=xyz"}
    with patch("mysolenso.services.stations.stationinfodev.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationInfoDevice(parent)
        obj._get_station_info_device()
        MockPost.return_value.set_headers.assert_called_with({"Cookie": "solenso_token=xyz"})
