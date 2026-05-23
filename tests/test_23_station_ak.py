"""Tests for MySolensoStationAK - station geolocation/AK data service."""
 
import pytest
from unittest.mock import MagicMock, patch
 
from mysolenso.services.stations.ak import MySolensoStationAK
from mysolenso.exceptions import MySolensoException
 
 
# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
 
FULL_RESPONSE = {
    "id": 9999999,
    "longitude": "39.10884652257048",
    "latitude": "-76.77128918829347",
    "address": "95 Moon Road, 99999 Galaxy, World",
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
 
 
def _make_station_ak(api_response=None) -> MySolensoStationAK:
    parent = _make_parent()
    response = api_response if api_response is not None else FULL_RESPONSE
    with patch("mysolenso.services.stations.ak.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoStationAK(parent)
        obj._get_station_ak()
        return obj
 
 
# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
 
def test_init_raises_when_no_station():
    """MySolensoStationAK raises if no active station is set."""
    parent = _make_parent(station_id=None)
    with pytest.raises(MySolensoException):
        MySolensoStationAK(parent)
 
 
def test_init_stores_station_id():
    parent = _make_parent(station_id=42)
    obj = MySolensoStationAK(parent)
    assert obj._station_id == 42
 
 
def test_init_stores_ak():
    parent = _make_parent(ak="my_ak_key")
    obj = MySolensoStationAK(parent)
    assert obj._station_ak == "my_ak_key"
 
 
# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
 
def test_all_data():
    obj = _make_station_ak()
    assert obj.all_data == FULL_RESPONSE
 
 
def test_id():
    obj = _make_station_ak()
    assert obj.id == 9999999
 
 
def test_longitude():
    obj = _make_station_ak()
    assert obj.longitude == "39.10884652257048"
 
 
def test_latitude():
    obj = _make_station_ak()
    assert obj.latitude == "-76.77128918829347"
 
 
def test_address():
    obj = _make_station_ak()
    assert obj.address == "95 Moon Road, 99999 Galaxy, World"
 
 
# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------
 
def test_set_station_invalid_raises():
    """set_station raises when the station ID is not in the account list."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}])
    with patch("mysolenso.services.stations.ak.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationAK(parent)
        obj._get_station_ak()
        with pytest.raises(MySolensoException):
            obj.set_station(999, ak="ak", refresh=False)
 
 
def test_set_station_updates_id_and_ak():
    """set_station stores the new station ID and AK key."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
    with patch("mysolenso.services.stations.ak.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationAK(parent)
        obj._get_station_ak()
        obj.set_station(43, ak="new_ak", refresh=False)
        assert obj._station_id == 43
        assert obj._station_ak == "new_ak"
 
 
def test_set_station_with_refresh_calls_api():
    """set_station with refresh=True triggers a new API call."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
    with patch("mysolenso.services.stations.ak.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationAK(parent)
        obj._get_station_ak()
        initial_count = MockPost.return_value.post.call_count
        obj.set_station(43, ak="ak2", refresh=True)
        assert MockPost.return_value.post.call_count > initial_count
 
 
# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------
 
def test_station_ak_refresh_calls_api():
    parent = _make_parent()
    with patch("mysolenso.services.stations.ak.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationAK(parent)
        obj._get_station_ak()
        obj.station_ak_refresh()
        assert MockPost.return_value.post.call_count >= 2
 
 
# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
 
def test_empty_response_raises():
    parent = _make_parent()
    with patch("mysolenso.services.stations.ak.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = {}
        obj = MySolensoStationAK(parent)
        with pytest.raises(MySolensoException):
            obj._get_station_ak()
 
 
def test_network_error_raises():
    parent = _make_parent()
    with patch("mysolenso.services.stations.ak.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("connection error")
        obj = MySolensoStationAK(parent)
        with pytest.raises(MySolensoException):
            obj._get_station_ak()
 
 
def test_headers_injected():
    parent = _make_parent()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=xyz"}
    with patch("mysolenso.services.stations.ak.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoStationAK(parent)
        obj._get_station_ak()
        MockPost.return_value.set_headers.assert_called_with({"Cookie": "solenso_token=xyz"})
 
 
def test_whitespace_stripped():
    """String fields are stripped of leading/trailing whitespace."""
    response = {
        "id": 42,
        "longitude": "  39.108  ",
        "latitude": "  -76.771  ",
        "address": "  Main Street  ",
    }
    obj = _make_station_ak(api_response=response)
    assert obj.longitude == "39.108"
    assert obj.latitude == "-76.771"
    assert obj.address == "Main Street"