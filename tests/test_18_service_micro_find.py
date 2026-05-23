"""Tests for MySolensoMicroFind - single microinverter detail service."""
 
import pytest
from unittest.mock import MagicMock, patch
 
from mysolenso.services.micro.find import MySolensoMicroFind
from mysolenso.exceptions import MySolensoException
 
 
# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
 
MICRO_ID = 9988950
 
MICROS_LIST = [
    {"sn": "A900016B5", "id": MICRO_ID},
    {"sn": "A900016B2", "id": 9988930},
]
 
FULL_RESPONSE = {
    "sn": "A900016B5",
    "warn_data": {"warn": False, "connect": True},
    "id": MICRO_ID,
    "sid": 9999999,
    "station_name": "DOE JOHN",
    "dev_type": 3,
    "tz_name": "UTC+01",
    "vc": "2L2",
    "init_soft_ver": "V01.00.04",
    "init_hard_no": "Sol-H1000H",
    "init_hard_ver": "H00.04.00",
    "dtu_id": 1238090,
    "dtu_sn": "D0900999H",
    "rule": {"port": 2, "phase": 1},
}
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _make_parent(station_id=42, micros_list=None):
    """Return a mock parent with station and dtuselectall stubs."""
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=tok"}
    parent.dtuselectall.list_micros = micros_list if micros_list is not None else MICROS_LIST
    return parent
 
 
def _make_micro_find(micro_id=MICRO_ID, api_response=None) -> MySolensoMicroFind:
    """Build a MySolensoMicroFind with set_micro already called."""
    parent = _make_parent()
    response = api_response if api_response is not None else FULL_RESPONSE
    with patch("mysolenso.services.micro.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoMicroFind(parent)
        obj.set_micro(micro_id, refresh=True)
        return obj
 
 
# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
 
def test_init_raises_when_no_station():
    """MySolensoMicroFind raises if no active station is set on the parent."""
    parent = _make_parent(station_id=None)
    with pytest.raises(MySolensoException):
        MySolensoMicroFind(parent)
 
 
def test_init_stores_station_id():
    """station_id is inherited from the parent at construction."""
    parent = _make_parent(station_id=77)
    obj = MySolensoMicroFind(parent)
    assert obj._station_id == 77
 
 
def test_init_micro_id_is_none():
    """_micro_id is None until set_micro is called."""
    parent = _make_parent()
    obj = MySolensoMicroFind(parent)
    assert obj._micro_id is None
 
 
# ---------------------------------------------------------------------------
# set_micro
# ---------------------------------------------------------------------------
 
def test_set_micro_valid():
    """set_micro stores the micro ID when it exists in the micro list."""
    parent = _make_parent()
    with patch("mysolenso.services.micro.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoMicroFind(parent)
        obj.set_micro(MICRO_ID, refresh=True)
        assert obj._micro_id == MICRO_ID
 
 
def test_set_micro_invalid_raises():
    """set_micro raises MySolensoException when the micro ID is not in the list."""
    parent = _make_parent()
    obj = MySolensoMicroFind(parent)
    with pytest.raises(MySolensoException):
        obj.set_micro(9999999, refresh=False)
 
 
def test_set_micro_no_refresh_skips_api():
    """set_micro with refresh=False does not call the API."""
    parent = _make_parent()
    with patch("mysolenso.services.micro.find.MySolensoPost") as MockPost:
        obj = MySolensoMicroFind(parent)
        obj.set_micro(MICRO_ID, refresh=False)
        MockPost.return_value.post.assert_not_called()
 
 
def test_set_micro_with_refresh_calls_api():
    """set_micro with refresh=True triggers an API call."""
    parent = _make_parent()
    with patch("mysolenso.services.micro.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoMicroFind(parent)
        obj.set_micro(MICRO_ID, refresh=True)
        MockPost.return_value.post.assert_called_once()
 
 
# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
 
def test_all_data():
    obj = _make_micro_find()
    assert obj.all_data == FULL_RESPONSE
 
 
def test_all_data_sn():
    obj = _make_micro_find()
    assert obj.all_data["sn"] == "A900016B5"
 
 
def test_all_data_connected():
    obj = _make_micro_find()
    assert obj.all_data["warn_data"]["connect"] is True
 
 
def test_all_data_dtu_sn():
    obj = _make_micro_find()
    assert obj.all_data["dtu_sn"] == "D0900999H"
 
 
# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
 
def test_get_micro_find_raises_when_micro_id_none():
    """_get_micro_find raises MySolensoException if _micro_id is None."""
    parent = _make_parent()
    obj = MySolensoMicroFind(parent)
    # _micro_id is None by default
    with pytest.raises(MySolensoException):
        obj._get_micro_find()
 
 
def test_empty_response_raises():
    """Empty API response raises MySolensoException."""
    parent = _make_parent()
    with patch("mysolenso.services.micro.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = {}
        obj = MySolensoMicroFind(parent)
        obj._micro_id = MICRO_ID
        with pytest.raises(MySolensoException):
            obj._get_micro_find()
 
 
def test_network_error_raises():
    """Network error during API call raises MySolensoException."""
    parent = _make_parent()
    with patch("mysolenso.services.micro.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("timeout")
        obj = MySolensoMicroFind(parent)
        obj._micro_id = MICRO_ID
        with pytest.raises(MySolensoException):
            obj._get_micro_find()
 
 
def test_headers_injected():
    """Auth headers from the parent are forwarded to MySolensoPost."""
    parent = _make_parent()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=xyz"}
    with patch("mysolenso.services.micro.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoMicroFind(parent)
        obj.set_micro(MICRO_ID, refresh=True)
        MockPost.return_value.set_headers.assert_called_with({"Cookie": "solenso_token=xyz"})