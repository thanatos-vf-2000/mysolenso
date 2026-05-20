"""Tests for MySolensoStationCountDevice — retrieving device count summary data for a station."""
 
import pytest
from unittest.mock import MagicMock, patch
 
from mysolenso.services.stations.countdevice import MySolensoStationCountDevice
from mysolenso.exceptions import MySolensoException
 
 
# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
 
FULL_RESPONSE = {
                    "sn": "AABBCCDD",
                    "station_num": 1,
                    "dtu_num": 1,
                    "repeater_num": 0,
                    "mi_num": 5,
                    "inv_num": 0,
                    "au_num": 0,
                    "rsd_num": 0,
                    "op_num": 0,
                    "tran_num": 0,
                    "meter_num": 0,
                    "bms_num": 0,
                    "em_num": 0
                }
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _make_parent(station_id=42, ak="ak_abc", stations=None):
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.ak = ak
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=tok"}
    return parent
 
 
def _make_station_countdevice(api_response=None) -> MySolensoStationCountDevice:
    parent = _make_parent()
    response = api_response if api_response is not None else FULL_RESPONSE
    with patch("mysolenso.services.stations.countdevice.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoStationCountDevice(parent)
        obj._get_station_count_device()
        return obj
 
 
# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
 
def test_init_raises_when_no_station():
    """MySolensoStationCountDevice raises if no active station is set."""
    parent = _make_parent(station_id=None)
    with pytest.raises(MySolensoException):
        MySolensoStationCountDevice(parent)
 
 
def test_init_stores_station_id():
    parent = _make_parent(station_id=42)
    obj = MySolensoStationCountDevice(parent)
    assert obj._station_id == 42
 
 
 
# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
 
def test_all_data():
    obj = _make_station_countdevice()
    assert obj.all_data == FULL_RESPONSE
 
 
def test_sn():
    obj = _make_station_countdevice()
    assert obj.sn == "AABBCCDD"
 
def test_station_num():
    obj = _make_station_countdevice()
    assert obj.station_num == 1
    
def test_dtu_num():
    obj = _make_station_countdevice()
    assert obj.dtu_num == 1

def test_repeater_num():
    obj = _make_station_countdevice()
    assert obj.repeater_num == 0

def test_mi_num():
    obj = _make_station_countdevice()
    assert obj.mi_num == 5

def test_au_num():
    obj = _make_station_countdevice()
    assert obj.au_num == 0

def test_rsd_num():
    obj = _make_station_countdevice()
    assert obj.rsd_num == 0

def test_op_num():
    obj = _make_station_countdevice()
    assert obj.op_num == 0

def test_tran_num():
    obj = _make_station_countdevice()
    assert obj.tran_num == 0

def test_meter_num():
    obj = _make_station_countdevice()
    assert obj.meter_num == 0

def test_bms_num():
    obj = _make_station_countdevice()
    assert obj.bms_num == 0

def test_em_num():
    obj = _make_station_countdevice()
    assert obj.em_num == 0
# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------
 
def test_set_station_invalid_raises():
    """set_station raises when the station ID is not in the account list."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}])
    with patch("mysolenso.services.stations.countdevice.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationCountDevice(parent)
        obj._get_station_count_device()
        with pytest.raises(MySolensoException):
            obj.set_station(id=999, refresh=False)
 
 
def test_set_station_updates_id():
    """set_station stores the new station ID and AK key."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
    with patch("mysolenso.services.stations.countdevice.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationCountDevice(parent)
        obj._get_station_count_device()
        obj.set_station(id=43, refresh=False)
        assert obj._station_id == 43
 
 
def test_set_station_with_refresh_calls_api():
    """set_station with refresh=True triggers a new API call."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
    with patch("mysolenso.services.stations.countdevice.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationCountDevice(parent)
        obj._get_station_count_device()
        initial_count = MockPost.return_value.post.call_count
        obj.set_station(id=43, refresh=True)
        assert MockPost.return_value.post.call_count > initial_count
 
 
# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------
 
def test_station_countdevice_refresh_calls_api():
    parent = _make_parent()
    with patch("mysolenso.services.stations.countdevice.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationCountDevice(parent)
        obj._get_station_count_device()
        obj.station_count_device_refresh()
        assert MockPost.return_value.post.call_count >= 1
 
 
# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
 
def test_empty_response_raises():
    parent = _make_parent()
    with patch("mysolenso.services.stations.countdevice.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = {}
        obj = MySolensoStationCountDevice(parent)
        with pytest.raises(MySolensoException):
            obj._get_station_count_device()
 
 
def test_network_error_raises():
    parent = _make_parent()
    with patch("mysolenso.services.stations.countdevice.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("connection error")
        obj = MySolensoStationCountDevice(parent)
        with pytest.raises(MySolensoException):
            obj._get_station_count_device()
 
 
def test_headers_injected():
    parent = _make_parent()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=xyz"}
    with patch("mysolenso.services.stations.countdevice.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationCountDevice(parent)
        obj._get_station_count_device()
        MockPost.return_value.set_headers.assert_called_with({"Cookie": "solenso_token=xyz"})
 